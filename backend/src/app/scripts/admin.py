# pyright: reportUnknownMemberType=false

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

import boto3

from app.runtime.handlers import Queue, Table, enqueue_job


class ReadTable(Table, Protocol):
    def get_item(self, **kwargs: object) -> dict[str, Any]: ...


class SqsAdmin(Protocol):
    def start_message_move_task(self, **kwargs: object) -> dict[str, Any]: ...


class S3Admin(Protocol):
    def put_object(self, **kwargs: object) -> object: ...


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="diopside-admin")
    subcommands = value.add_subparsers(dest="command", required=True)

    start = subcommands.add_parser("start-job")
    start.add_argument("job_type")
    start.add_argument("target_id")
    start.add_argument("input_version")
    start.add_argument("--manifest", type=Path)
    start.add_argument("--yes", action="store_true")

    status = subcommands.add_parser("get-job")
    status.add_argument("job_id")

    cancel = subcommands.add_parser("cancel-job")
    cancel.add_argument("job_id")
    cancel.add_argument("--yes", action="store_true")

    redrive = subcommands.add_parser("redrive-dlq")
    redrive.add_argument("source_arn")
    redrive.add_argument("destination_arn")
    redrive.add_argument("--rate", type=int, default=10)
    redrive.add_argument("--yes", action="store_true")

    gates = subcommands.add_parser("replace-gates")
    gates.add_argument("evidence", type=Path)
    gates.add_argument("--yes", action="store_true")

    deletion = subcommands.add_parser("request-deletion")
    deletion.add_argument("video_id")
    deletion.add_argument("--reason", required=True)
    deletion.add_argument("--yes", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "get-job":
        result = _get_job(args.job_id)
    else:
        _confirmed(args)
        if args.command == "start-job":
            manifest = _load_object(args.manifest) if args.manifest else {}
            result = _start_job(args.job_type, args.target_id, args.input_version, manifest)
        elif args.command == "cancel-job":
            result = _cancel_job(args.job_id)
        elif args.command == "redrive-dlq":
            result = _redrive(args.source_arn, args.destination_arn, args.rate)
        elif args.command == "replace-gates":
            result = _replace_gates(_load_object(args.evidence))
        elif args.command == "request-deletion":
            result = _request_deletion(args.video_id, args.reason)
        else:
            raise AssertionError("unreachable command")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def _start_job(
    job_type: str, target_id: str, input_version: str, manifest: dict[str, Any]
) -> dict[str, Any]:
    table = cast(Table, boto3.resource("dynamodb").Table(_env("CONTROL_TABLE")))
    queue_name = "EXPORT_QUEUE_URL" if job_type == "static_export" else "JOB_QUEUE_URL"
    queue = cast(Queue, boto3.resource("sqs").Queue(_env(queue_name)))
    return enqueue_job(
        {
            "jobType": job_type,
            "targetId": target_id,
            "inputVersion": input_version,
            "inputManifest": manifest,
        },
        table,
        queue,
    )


def _get_job(job_id: str) -> dict[str, Any]:
    table = cast(ReadTable, boto3.resource("dynamodb").Table(_env("CONTROL_TABLE")))
    response = table.get_item(Key={"pk": f"JOB#{job_id}", "sk": "EVENT#0001"})
    item = response.get("Item")
    if not isinstance(item, dict):
        raise SystemExit(f"job not found: {job_id}")
    return cast(dict[str, Any], item)


def _cancel_job(job_id: str) -> dict[str, Any]:
    table = cast(ReadTable, boto3.resource("dynamodb").Table(_env("CONTROL_TABLE")))
    table.update_item(
        Key={"pk": f"JOB#{job_id}", "sk": "EVENT#0001"},
        UpdateExpression="SET #status = :cancelled",
        ConditionExpression="#status IN (:queued, :running)",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":queued": "queued",
            ":running": "running",
            ":cancelled": "cancelled",
        },
    )
    return {"jobId": job_id, "status": "cancelled"}


def _redrive(source_arn: str, destination_arn: str, rate: int) -> dict[str, Any]:
    if rate < 1 or rate > 500:
        raise SystemExit("--rate must be 1..500")
    client = cast(SqsAdmin, boto3.client("sqs"))
    return client.start_message_move_task(
        SourceArn=source_arn,
        DestinationArn=destination_arn,
        MaxNumberOfMessagesPerSecond=rate,
    )


def _replace_gates(evidence: dict[str, Any]) -> dict[str, Any]:
    gates = evidence.get("gates")
    gate_ids: set[str] = (
        set(cast(dict[str, Any], gates)) if isinstance(gates, dict) else set()
    )
    if gate_ids != {
        f"GATE-{number:03d}" for number in range(1, 7)
    }:
        raise SystemExit("evidence must contain exactly GATE-001..GATE-006")
    body = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    cast(S3Admin, boto3.client("s3")).put_object(
        Bucket=_env("CONFIGURATION_BUCKET"),
        Key="gates/current.json",
        Body=body,
        ContentType="application/json",
    )
    return {"key": "gates/current.json", "bytes": len(body)}


def _request_deletion(video_id: str, reason: str) -> dict[str, Any]:
    if not video_id or not reason.strip():
        raise SystemExit("video_id and --reason are required")
    requested_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return _start_job(
        "static_export",
        video_id,
        f"deletion:{requested_at}",
        {
            "purgeTrigger": f"deletion:{video_id}",
            "excludeVideoIds": [video_id],
            "reason": reason.strip(),
            "requestedAt": requested_at,
        },
    )


def _load_object(path: Path) -> dict[str, Any]:
    value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON object required: {path}")
    return cast(dict[str, Any], value)


def _confirmed(args: argparse.Namespace) -> None:
    if args.yes is not True:
        raise SystemExit("state-changing command requires --yes")


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"{name} is required")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
