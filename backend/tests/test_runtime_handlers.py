from typing import Any

from app.runtime.handlers import enqueue_job, processor_handler


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
    assert len(table.updates) == 1


class FakeDynamo:
    def __init__(self, table: FakeTable) -> None:
        self.table = table

    def Table(self, _name: str) -> FakeTable:
        return self.table
