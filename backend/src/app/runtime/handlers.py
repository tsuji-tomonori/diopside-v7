# pyright: reportUnknownMemberType=false

from __future__ import annotations

import json
import os
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Protocol, cast

import boto3
from botocore.exceptions import ClientError

from app.operations.policy import JobType, canonical_job_key

JobExecutor = Callable[[dict[str, Any]], dict[str, Any] | None]


class PermanentJobError(ValueError):
    """A malformed or unsupported job that must not be retried by SQS."""


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
    now_value = datetime.now(UTC).replace(second=0, microsecond=0)
    if input_version == "scheduled" or input_version.startswith("scheduled:"):
        bucket_value = event.get("scheduleBucketMinutes", 5)
        if not isinstance(bucket_value, int) or bucket_value < 1 or bucket_value > 1440:
            raise ValueError("scheduleBucketMinutes must be 1..1440")
        minute = now_value.minute - (now_value.minute % bucket_value)
        timestamp = now_value.replace(minute=minute).isoformat().replace("+00:00", "Z")
        input_version = f"{input_version}:{timestamp}"
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
    return process_records(event, table, dispatch_job)


def process_records(
    event: dict[str, Any], table: Table, executor: JobExecutor
) -> dict[str, Any]:
    failures: list[dict[str, str]] = []
    records = event.get("Records", [])
    if not isinstance(records, list):
        raise ValueError("Records must be an array")
    for raw in cast(list[object], records):
        job: dict[str, Any] | None = None
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
            output = executor(job) or {}
            _mark_finished(table, job, "succeeded", output=output)
        except PermanentJobError as error:
            if job is not None:
                _mark_finished(table, job, "failed_permanent", error=error)
        except (KeyError, ValueError, json.JSONDecodeError, ClientError, RuntimeError) as error:
            if job is not None and isinstance(job.get("jobId"), str):
                _mark_finished(table, job, "failed_retryable", error=error)
            if isinstance(message_id, str):
                failures.append({"itemIdentifier": message_id})
    return {"batchItemFailures": failures}


def dispatch_job(job: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a runtime job to its configured domain handler.

    Domain handlers are supplied as ``module:function`` environment values. This keeps
    orchestration independent from collection/processing implementations and makes a
    missing production binding a permanent, observable configuration failure.
    """
    job_type = job.get("jobType")
    if not isinstance(job_type, str) or job_type not in {item.value for item in JobType}:
        raise PermanentJobError("invalid jobType")
    binding = os.environ.get(f"JOB_HANDLER_{job_type.upper()}")
    if not binding:
        raise PermanentJobError(f"handler is not configured for {job_type}")
    module_name, separator, function_name = binding.partition(":")
    if not separator or not module_name or not function_name:
        raise PermanentJobError(f"invalid handler binding for {job_type}")
    from importlib import import_module

    function = getattr(import_module(module_name), function_name, None)
    if not callable(function):
        raise PermanentJobError(f"handler is not callable for {job_type}")
    result = function(job)
    if result is None:
        return {}
    if not isinstance(result, dict):
        raise PermanentJobError(f"handler returned a non-object for {job_type}")
    return cast(dict[str, Any], result)


def exporter_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    if "Records" in event:
        table = cast(Table, boto3.resource("dynamodb").Table(_required_env("CONTROL_TABLE")))
        return process_records(event, table, dispatch_job)
    event = {**event, "jobType": JobType.STATIC_EXPORT.value}
    table = cast(Table, boto3.resource("dynamodb").Table(_required_env("CONTROL_TABLE")))
    queue = cast(Queue, boto3.resource("sqs").Queue(_required_env("EXPORT_QUEUE_URL")))
    return enqueue_job(event, table, queue)


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


def _mark_finished(
    table: Table,
    job: dict[str, Any],
    status: str,
    *,
    output: dict[str, Any] | None = None,
    error: BaseException | None = None,
) -> None:
    job_id = job.get("jobId")
    if not isinstance(job_id, str):
        raise ValueError("jobId is required")
    values: dict[str, object] = {
        ":running": "running",
        ":status": status,
        ":finished": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    expression = "SET #status = :status, finishedAt = :finished"
    if output is not None:
        expression += ", outputManifest = :output"
        values[":output"] = output
    if error is not None:
        expression += ", errorType = :errorType, errorMessage = :errorMessage"
        values[":errorType"] = type(error).__name__
        values[":errorMessage"] = str(error)[:1000]
    table.update_item(
        Key={"pk": f"JOB#{job_id}", "sk": "EVENT#0001"},
        UpdateExpression=expression,
        ConditionExpression="#status = :running",
        ExpressionAttributeNames={"#status": "status"},
        ExpressionAttributeValues=values,
    )


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value
