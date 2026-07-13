from typing import Any

from app.operations.policy import PolicyStopped
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
    """ジョブが送信前に永続化されることを検証する。"""
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


def test_scheduled_input_version_is_time_bucketed() -> None:
    """定期実行入力のversionが時間枠単位になることを検証する。"""
    table = FakeTable()
    queue = FakeQueue()
    enqueue_job(
        {
            "jobType": "metadata_sync",
            "targetId": "channel",
            "inputVersion": "scheduled:live",
            "scheduleBucketMinutes": 5,
        },
        table,
        queue,
    )
    version = table.items[0]["Item"]["inputVersion"]
    assert isinstance(version, str)
    assert version.startswith("scheduled:live:")
    assert version.endswith("Z")


def test_processor_returns_partial_batch_failures(monkeypatch: Any) -> None:
    """processorが部分的なbatch失敗を返すことを検証する。"""
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
    """レコード処理が成功と再試行可能失敗を記録することを検証する。"""
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
    """永続的失敗を再試行しないことを検証する。"""
    table = FakeTable()

    def execute(_job: dict[str, Any]) -> None:
        raise PermanentJobError("unsupported")

    result = process_records(
        {"Records": [{"messageId": "bad", "body": '{"jobId":"bad"}'}]}, table, execute
    )
    assert result == {"batchItemFailures": []}
    assert table.updates[-1]["ExpressionAttributeValues"][":status"] == "failed_permanent"


def test_process_records_schedules_bounded_retry() -> None:
    """上限付き再試行を予定することを検証する。"""
    table = FakeTable()
    retry = FakeQueue()
    dead_letter = FakeQueue()

    def execute(_job: dict[str, Any]) -> None:
        raise RuntimeError("temporary")

    result = process_records(
        {
            "Records": [
                {
                    "messageId": "retry",
                    "body": '{"jobId":"retry","attempt":1}',
                }
            ]
        },
        table,
        execute,
        retry,
        dead_letter,
    )
    assert result == {"batchItemFailures": []}
    assert len(retry.messages) == 1
    assert 0 <= retry.messages[0]["DelaySeconds"] <= 2
    assert '"attempt":2' in retry.messages[0]["MessageBody"]
    assert dead_letter.messages == []


def test_process_records_sends_exhausted_attempt_to_dlq() -> None:
    """再試行上限に達したレコードをDLQへ送ることを検証する。"""
    table = FakeTable()
    retry = FakeQueue()
    dead_letter = FakeQueue()

    def execute(_job: dict[str, Any]) -> None:
        raise RuntimeError("temporary")

    result = process_records(
        {
            "Records": [
                {
                    "messageId": "retry",
                    "body": '{"jobId":"retry","attempt":4}',
                }
            ]
        },
        table,
        execute,
        retry,
        dead_letter,
    )
    assert result == {"batchItemFailures": []}
    assert retry.messages == []
    assert len(dead_letter.messages) == 1


def test_policy_stop_is_cancelled_without_retry_or_dlq() -> None:
    """ポリシー停止を再試行やDLQ送信なしで取消扱いにすることを検証する。"""
    table = FakeTable()
    retry = FakeQueue()
    dead_letter = FakeQueue()

    def execute(_job: dict[str, Any]) -> None:
        raise PolicyStopped("quota")

    result = process_records(
        {"Records": [{"messageId": "stop", "body": '{"jobId":"stop"}'}]},
        table,
        execute,
        retry,
        dead_letter,
    )
    assert result == {"batchItemFailures": []}
    assert retry.messages == []
    assert dead_letter.messages == []
    assert table.updates[-1]["ExpressionAttributeValues"][":status"] == "cancelled"


class FakeDynamo:
    def __init__(self, table: FakeTable) -> None:
        self.table = table

    def Table(self, _name: str) -> FakeTable:
        return self.table
