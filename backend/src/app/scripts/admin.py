# pyright: reportUnknownMemberType=false

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol, cast

import boto3
from botocore.exceptions import ClientError

from app.exporter.publisher import ReleaseValidator
from app.runtime.handlers import Queue, Table, enqueue_job


class ReadTable(Table, Protocol):
    def get_item(self, **kwargs: object) -> dict[str, Any]: ...

    def scan(self, **kwargs: object) -> dict[str, Any]: ...


class SqsAdmin(Protocol):
    def start_message_move_task(self, **kwargs: object) -> dict[str, Any]: ...


class S3Admin(Protocol):
    def put_object(self, **kwargs: object) -> object: ...

    def get_object(self, **kwargs: object) -> dict[str, Any]: ...

    def list_objects_v2(self, **kwargs: object) -> dict[str, Any]: ...

    def delete_objects(self, **kwargs: object) -> object: ...


class SqsReport(Protocol):
    def get_queue_attributes(self, **kwargs: object) -> dict[str, Any]: ...


class CostReport(Protocol):
    def get_cost_and_usage(self, **kwargs: object) -> dict[str, Any]: ...


class ReadableBody(Protocol):
    def read(self) -> bytes: ...


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
    gates.add_argument("--reason", required=True)
    gates.add_argument("--yes", action="store_true")

    deletion = subcommands.add_parser("request-deletion")
    deletion.add_argument("video_id")
    deletion.add_argument("--reason", required=True)
    deletion.add_argument("--yes", action="store_true")

    summary = subcommands.add_parser("operations-summary")
    summary.add_argument("--from", dest="from_date", required=True)
    summary.add_argument("--to", dest="to_date", required=True)

    publish = subcommands.add_parser("publish-candidate")
    publish.add_argument("directory", type=Path)
    publish.add_argument("--yes", action="store_true")
    return value


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "get-job":
        result = _get_job(args.job_id)
    elif args.command == "operations-summary":
        result = _operations_summary(args.from_date, args.to_date)
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
            result = _replace_gates(_load_object(args.evidence), args.reason)
        elif args.command == "request-deletion":
            result = _request_deletion(args.video_id, args.reason)
        elif args.command == "publish-candidate":
            result = _publish_candidate(args.directory)
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


def _replace_gates(evidence: dict[str, Any], reason: str) -> dict[str, Any]:
    gates = evidence.get("gates")
    gate_ids: set[str] = (
        set(cast(dict[str, Any], gates)) if isinstance(gates, dict) else set()
    )
    if gate_ids != {
        f"GATE-{number:03d}" for number in range(1, 7)
    }:
        raise SystemExit("evidence must contain exactly GATE-001..GATE-006")
    evidence_id = evidence.get("evidenceId")
    if not isinstance(evidence_id, str) or not evidence_id:
        raise SystemExit("evidenceId is required")
    if not reason.strip():
        raise SystemExit("--reason is required")
    body = json.dumps(evidence, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    bucket = _env("CONFIGURATION_BUCKET")
    client = cast(S3Admin, boto3.client("s3"))
    replaced_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    history_key: str | None = None
    try:
        current_response = client.get_object(Bucket=bucket, Key="gates/current.json")
        previous = cast(ReadableBody, current_response.get("Body")).read()
        previous_document = cast(object, json.loads(previous))
        if isinstance(previous_document, dict):
            archived = {
                **cast(dict[str, Any], previous_document),
                "supersededAt": replaced_at,
                "replacementEvidenceId": evidence_id,
                "supersessionReason": reason.strip(),
            }
            previous_id = str(archived.get("evidenceId", "unknown"))
            history_key = f"gates/history/{replaced_at.replace(':', '')}-{previous_id}.json"
            client.put_object(
                Bucket=bucket,
                Key=history_key,
                Body=json.dumps(
                    archived, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ).encode(),
                ContentType="application/json",
            )
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code not in {"NoSuchKey", "404", "NotFound"}:
            raise
    client.put_object(
        Bucket=bucket,
        Key="gates/current.json",
        Body=body,
        ContentType="application/json",
    )
    table = cast(Table, boto3.resource("dynamodb").Table(_env("CONTROL_TABLE")))
    table.put_item(
        Item={
            "pk": f"AUDIT#{replaced_at}",
            "sk": f"GATE_REPLACEMENT#{evidence_id}",
            "action": "replace_gate_evidence",
            "evidenceId": evidence_id,
            "reason": reason.strip(),
            "occurredAt": replaced_at,
            "historyKey": history_key or "none",
        },
        ConditionExpression="attribute_not_exists(pk)",
    )
    return {
        "key": "gates/current.json",
        "historyKey": history_key,
        "evidenceId": evidence_id,
        "bytes": len(body),
    }


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


def _publish_candidate(directory: Path) -> dict[str, Any]:
    validation = ReleaseValidator().validate(directory)
    bucket = _env("PROCESSED_BUCKET")
    prefix = "candidates/latest"
    client = cast(S3Admin, boto3.client("s3"))
    _clear_s3_prefix(client, bucket, f"{prefix}/")
    artifact_count = 0
    for path in sorted(value for value in directory.rglob("*") if value.is_file()):
        relative = path.relative_to(directory).as_posix()
        content_type = "image/svg+xml" if path.suffix == ".svg" else "application/json"
        client.put_object(
            Bucket=bucket,
            Key=f"{prefix}/{relative}",
            Body=path.read_bytes(),
            ContentType=content_type,
        )
        artifact_count += 1
    job = _start_job(
        "static_export",
        validation.release_id,
        f"candidate:{validation.release_id}",
        {"bucket": bucket, "candidatePrefix": prefix},
    )
    return {
        **job,
        "releaseId": validation.release_id,
        "videoCount": validation.video_count,
        "artifactCount": artifact_count,
    }


def _clear_s3_prefix(client: S3Admin, bucket: str, prefix: str) -> None:
    token: str | None = None
    while True:
        arguments: dict[str, object] = {"Bucket": bucket, "Prefix": prefix}
        if token:
            arguments["ContinuationToken"] = token
        page = client.list_objects_v2(**arguments)
        contents = page.get("Contents", [])
        objects = [
            {"Key": key}
            for raw in cast(list[object], contents)
            if isinstance(contents, list) and isinstance(raw, dict)
            for key in [cast(dict[str, Any], raw).get("Key")]
            if isinstance(key, str)
        ]
        if objects:
            client.delete_objects(Bucket=bucket, Delete={"Objects": objects, "Quiet": True})
        next_value = page.get("NextContinuationToken")
        token = next_value if isinstance(next_value, str) else None
        if token is None:
            return


def _operations_summary(from_date: str, to_date: str) -> dict[str, Any]:
    start = datetime.fromisoformat(from_date).date()
    end = datetime.fromisoformat(to_date).date()
    if end <= start or (end - start).days > 31:
        raise SystemExit("summary range must be 1..31 days and --to is exclusive")
    generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    table = cast(ReadTable, boto3.resource("dynamodb").Table(_env("CONTROL_TABLE")))
    items = _scan_all(table)
    jobs = [item for item in items if str(item.get("pk", "")).startswith("JOB#")]
    statuses = Counter(str(item.get("status", "unknown")) for item in jobs)
    terminal = sum(statuses[name] for name in ("succeeded", "failed_permanent", "cancelled"))
    success_rate = statuses["succeeded"] / terminal if terminal else None

    sqs = cast(SqsReport, boto3.client("sqs"))
    queue_depth = {
        name: _queue_depth(sqs, _env(variable))
        for name, variable in (
            ("jobs", "JOB_QUEUE_URL"),
            ("exports", "EXPORT_QUEUE_URL"),
            ("dlq", "DEAD_LETTER_QUEUE_URL"),
        )
    }
    s3 = cast(S3Admin, boto3.client("s3"))
    storage = {
        name: _bucket_usage(s3, value)
        for name, variable in (
            ("raw", "RAW_BUCKET"),
            ("processed", "PROCESSED_BUCKET"),
            ("public", "PUBLIC_BUCKET"),
            ("configuration", "CONFIGURATION_BUCKET"),
        )
        for value in [os.environ.get(variable)]
        if value
    }
    latest = _optional_s3_json(s3, os.environ.get("PUBLIC_BUCKET"), "data/latest.json")
    gates = _optional_s3_json(
        s3, os.environ.get("CONFIGURATION_BUCKET"), "gates/current.json"
    )
    cost: object = "unknown"
    try:
        response = cast(CostReport, boto3.client("ce")).get_cost_and_usage(
            TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
        cost = response.get("ResultsByTime", "unknown")
    except Exception:
        cost = "unknown"
    quota = [item for item in items if str(item.get("pk", "")).startswith("QUOTA#")]
    return cast(
        dict[str, Any],
        _json_safe(
            {
            "schemaVersion": "1.0.0",
            "generatedAt": generated_at,
            "window": {"from": start.isoformat(), "to": end.isoformat()},
            "jobs": {
                "total": len(jobs),
                "statusCounts": dict(statuses),
                "successRate": success_rate if success_rate is not None else "unknown",
            },
            "quota": quota,
            "queues": queue_depth,
            "storage": storage,
            "latestExport": latest if latest is not None else "unknown",
            "gates": gates if gates is not None else "unknown",
            "costByService": cost,
            }
        ),
    )


def _scan_all(table: ReadTable) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    start_key: dict[str, Any] | None = None
    while True:
        response = table.scan(**({"ExclusiveStartKey": start_key} if start_key else {}))
        raw_items = response.get("Items", [])
        if isinstance(raw_items, list):
            items.extend(
                cast(dict[str, Any], item)
                for item in cast(list[object], raw_items)
                if isinstance(item, dict)
            )
        next_key = response.get("LastEvaluatedKey")
        start_key = cast(dict[str, Any], next_key) if isinstance(next_key, dict) else None
        if start_key is None:
            return items


def _queue_depth(client: SqsReport, url: str) -> dict[str, int | str]:
    response = client.get_queue_attributes(
        QueueUrl=url,
        AttributeNames=[
            "ApproximateNumberOfMessages",
            "ApproximateNumberOfMessagesNotVisible",
        ],
    )
    attributes = response.get("Attributes", {})
    if not isinstance(attributes, dict):
        return {"visible": "unknown", "inFlight": "unknown"}
    values = cast(dict[str, Any], attributes)
    return {
        "visible": int(values.get("ApproximateNumberOfMessages", 0)),
        "inFlight": int(values.get("ApproximateNumberOfMessagesNotVisible", 0)),
    }


def _bucket_usage(client: S3Admin, bucket: str) -> dict[str, int]:
    count = 0
    size = 0
    token: str | None = None
    while True:
        arguments: dict[str, object] = {"Bucket": bucket}
        if token:
            arguments["ContinuationToken"] = token
        page = client.list_objects_v2(**arguments)
        contents = page.get("Contents", [])
        if isinstance(contents, list):
            for raw in cast(list[object], contents):
                if isinstance(raw, dict):
                    item = cast(dict[str, Any], raw)
                    count += 1
                    value = item.get("Size")
                    size += value if isinstance(value, int) else 0
        next_value = page.get("NextContinuationToken")
        token = next_value if isinstance(next_value, str) else None
        if not token:
            return {"objects": count, "bytes": size}


def _optional_s3_json(
    client: S3Admin, bucket: str | None, key: str
) -> dict[str, Any] | None:
    if not bucket:
        return None
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        raw = cast(ReadableBody, response.get("Body")).read()
        value = cast(object, json.loads(raw))
        return cast(dict[str, Any], value) if isinstance(value, dict) else None
    except Exception:
        return None


def _json_safe(value: object) -> object:
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in cast(dict[object, object], value).items()
        }
    if isinstance(value, list):
        return [_json_safe(item) for item in cast(list[object], value)]
    return value


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
