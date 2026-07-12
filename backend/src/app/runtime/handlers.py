# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any, Protocol, cast

import boto3
from botocore.exceptions import ClientError

from app.operations.policy import JobType, canonical_job_key


class Table(Protocol):
    def put_item(self, **kwargs: object) -> object: ...

    def update_item(self, **kwargs: object) -> object: ...


class Queue(Protocol):
    def send_message(self, **kwargs: object) -> object: ...


def collector_handler(event: dict[str, Any], _context: object) -> dict[str, Any]:
    table = cast(Table, boto3.resource("dynamodb").Table(_required_env("CONTROL_TABLE")))
    queue = cast(Queue, boto3.resource("sqs").Queue(_required_env("JOB_QUEUE_URL")))
    return enqueue_job(event, table, queue)


def enqueue_job(event: dict[str, Any], table: Table, queue: Queue) -> dict[str, Any]:
    job_type_value = event.get("jobType")
    target_id = event.get("targetId")
    input_version = event.get("inputVersion")
    if not isinstance(job_type_value, str) or job_type_value not in {
        item.value for item in JobType
    }:
        raise ValueError("invalid jobType")
    if not isinstance(target_id, str) or not target_id:
        raise ValueError("targetId is required")
    if not isinstance(input_version, str) or not input_version:
        raise ValueError("inputVersion is required")
    key = canonical_job_key(job_type_value, target_id, input_version)
    now = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    item: dict[str, Any] = {
        "pk": f"JOB#{key}",
        "sk": "EVENT#0001",
        "jobId": key,
        "canonicalJobKey": key,
        "jobType": job_type_value,
        "targetId": target_id,
        "inputVersion": input_version,
        "status": "queued",
        "attempt": 1,
        "queuedAt": now,
        "inputManifest": cast(object, event.get("inputManifest", {})),
        "correlationId": event.get("correlationId", key),
        "quotaUnitsByMethod": {},
    }
    try:
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(pk)")
    except ClientError as error:
        code = error.response.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            return {"jobId": key, "duplicate": True}
        raise
    queue.send_message(MessageBody=json.dumps(item, separators=(",", ":"), sort_keys=True))
    return {"jobId": key, "duplicate": False}


def processor_handler(event: dict[str, Any], _context: object) -> dict[str, Any]:
    table = cast(Table, boto3.resource("dynamodb").Table(_required_env("CONTROL_TABLE")))
    failures: list[dict[str, str]] = []
    records = event.get("Records", [])
    if not isinstance(records, list):
        raise ValueError("Records must be an array")
    for raw in cast(list[object], records):
        if not isinstance(raw, dict):
            continue
        record = cast(dict[str, Any], raw)
        message_id = record.get("messageId")
        try:
            body = json.loads(cast(str, record["body"]))
            if not isinstance(body, dict):
                raise ValueError("job body must be an object")
            job = cast(dict[str, Any], body)
            _mark_running(table, job)
        except (KeyError, ValueError, json.JSONDecodeError, ClientError):
            if isinstance(message_id, str):
                failures.append({"itemIdentifier": message_id})
    return {"batchItemFailures": failures}


def exporter_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    event = {**event, "jobType": JobType.STATIC_EXPORT.value}
    return collector_handler(event, context)


def _mark_running(table: Table, job: dict[str, Any]) -> None:
    job_id = job.get("jobId")
    if not isinstance(job_id, str):
        raise ValueError("jobId is required")
    table.update_item(
        Key={"pk": f"JOB#{job_id}", "sk": "EVENT#0001"},
        UpdateExpression="SET #status = :running, startedAt = :started",
        ConditionExpression="#status = :queued",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues={
            ":queued": "queued",
            ":running": "running",
            ":started": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        },
    )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value
