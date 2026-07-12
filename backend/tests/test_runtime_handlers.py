from typing import Any

from app.runtime.handlers import PermanentJobError, enqueue_job, process_records, processor_handler


class FakeTable:
    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []
        self.updates: list[dict[str, Any]] = []

    def put_item(self, **kwargs: object) -> object:
        self.items.append(kwargs)
        return {}

    def update_item(self, **kwargs: object) -> object:
        self.updates.append(kwargs)
        return {}


class FakeQueue:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def send_message(self, **kwargs: object) -> object:
        self.messages.append(kwargs)
        return {}


def test_enqueue_job_persists_before_sending() -> None:
    table = FakeTable()
    queue = FakeQueue()
    result = enqueue_job(
        {"jobType": "metadata_sync", "targetId": "channel", "inputVersion": "v1"},
        table,
        queue,
    )
    assert result["duplicate"] is False
    assert len(table.items) == 1
    assert len(queue.messages) == 1


def test_processor_returns_partial_batch_failures(monkeypatch: Any) -> None:
    table = FakeTable()
    monkeypatch.setenv("CONTROL_TABLE", "table")

    def resource(_name: str) -> FakeDynamo:
        return FakeDynamo(table)

    monkeypatch.setattr("app.runtime.handlers.boto3.resource", resource)
    result = processor_handler(
        {
            "Records": [
                {"messageId": "ok", "body": '{"jobId":"one"}'},
                {"messageId": "bad", "body": "not-json"},
            ]
        },
        None,
    )
    assert result == {"batchItemFailures": [{"itemIdentifier": "bad"}]}
    assert len(table.updates) == 2
    assert table.updates[-1]["ExpressionAttributeValues"][":status"] == "failed_permanent"


def test_process_records_marks_success_and_retryable_failure() -> None:
    table = FakeTable()

    def execute(job: dict[str, Any]) -> dict[str, Any]:
        if job["jobId"] == "retry":
            raise RuntimeError("temporary")
        return {"objectKey": "processed/result.json"}

    result = process_records(
        {
            "Records": [
                {"messageId": "ok", "body": '{"jobId":"ok"}'},
                {"messageId": "retry", "body": '{"jobId":"retry"}'},
            ]
        },
        table,
        execute,
    )
    assert result == {"batchItemFailures": [{"itemIdentifier": "retry"}]}
    statuses = [update["ExpressionAttributeValues"].get(":status") for update in table.updates]
    assert statuses == [None, "succeeded", None, "failed_retryable"]


def test_process_records_does_not_retry_permanent_failure() -> None:
    table = FakeTable()

    def execute(_job: dict[str, Any]) -> None:
        raise PermanentJobError("unsupported")

    result = process_records(
        {"Records": [{"messageId": "bad", "body": '{"jobId":"bad"}'}]}, table, execute
    )
    assert result == {"batchItemFailures": []}
    assert table.updates[-1]["ExpressionAttributeValues"][":status"] == "failed_permanent"


class FakeDynamo:
    def __init__(self, table: FakeTable) -> None:
        self.table = table

    def Table(self, _name: str) -> FakeTable:
        return self.table
