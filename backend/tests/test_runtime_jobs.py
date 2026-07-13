from io import BytesIO
from typing import Any, cast

import pytest

from app.collectors.youtube import JsonCheckpoint, LiveChatCollectionResult
from app.runtime import jobs


class FakeYouTube:
    def __enter__(self) -> "FakeYouTube":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def channel(self, channel_id: str) -> dict[str, Any]:
        assert channel_id == "channel-1"
        return {"contentDetails": {"relatedPlaylists": {"uploads": "playlist-1"}}}

    def uploads(self, playlist_id: str, *, max_pages: int | None = None) -> list[dict[str, Any]]:
        assert playlist_id == "playlist-1"
        assert max_pages is None
        return [{"contentDetails": {"videoId": "video-1"}}]

    def videos(self, video_ids: list[str]) -> list[dict[str, Any]]:
        assert video_ids == ["video-1"]
        return [{"id": "video-1"}]

    def quota_report(self) -> dict[str, Any]:
        return {"totalUnits": 3, "events": []}


class FakeS3:
    def __init__(self) -> None:
        self.puts: list[dict[str, object]] = []
        self.objects: dict[tuple[str, str], bytes] = {}

    def put_object(self, **kwargs: object) -> object:
        self.puts.append(kwargs)
        self.objects[(cast(str, kwargs["Bucket"]), cast(str, kwargs["Key"]))] = cast(
            bytes, kwargs["Body"]
        )
        return {}

    def get_object(self, **kwargs: object) -> dict[str, Any]:
        body = self.objects[(cast(str, kwargs["Bucket"]), cast(str, kwargs["Key"]))]
        return {"Body": BytesIO(body)}


class FakeLiveYouTube:
    def __enter__(self) -> "FakeLiveYouTube":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def collect_live_chat(
        self, live_chat_id: str, checkpoint: JsonCheckpoint, *, max_pages: int
    ) -> LiveChatCollectionResult:
        assert live_chat_id == "chat-1"
        assert checkpoint.load()["status"] == "running"
        assert max_pages == 3
        checkpoint.save({"status": "checkpointed", "messageIds": ["m1"]})
        return LiveChatCollectionResult("checkpointed", [], "next", 1000)

    def quota_report(self) -> dict[str, Any]:
        return {"totalUnits": 5, "events": []}


class FakeControl:
    def __init__(self, used: int) -> None:
        self.used = used
        self.updates: list[dict[str, object]] = []

    def get_item(self, **_kwargs: object) -> dict[str, Any]:
        return {"Item": {"used": self.used}}

    def update_item(self, **kwargs: object) -> object:
        self.updates.append(kwargs)
        return {}


def test_metadata_sync_collects_and_writes_raw_snapshot(monkeypatch: Any) -> None:
    store = FakeS3()

    def client(_service: str) -> FakeS3:
        return store

    def enqueue_child(*_args: object) -> None:
        return None

    def record_quota(*_args: object) -> None:
        return None

    def reserve_quota(*_args: object) -> int:
        return 1

    monkeypatch.setenv("RAW_BUCKET", "raw-bucket")
    monkeypatch.setattr(jobs, "_youtube", lambda: FakeYouTube())
    monkeypatch.setattr(jobs.boto3, "client", client)
    monkeypatch.setattr(jobs, "_enqueue_child", enqueue_child)
    monkeypatch.setattr(jobs, "_record_quota", record_quota)
    monkeypatch.setattr(jobs, "reserve_quota", reserve_quota)

    result = jobs.metadata_sync(
        {
            "jobId": "job-1",
            "targetId": "channel-1",
            "inputVersion": "scheduled-v1",
        }
    )

    assert result["bucket"] == "raw-bucket"
    assert result["key"] == "raw/metadata/channel-1/scheduled-v1/job-1.json"
    assert b'"video-1"' in cast(bytes, store.puts[0]["Body"])


def test_quota_reservation_stops_low_priority_at_80_percent(monkeypatch: Any) -> None:
    control = FakeControl(8000)

    def table() -> FakeControl:
        return control

    monkeypatch.setattr(jobs, "_control_table", table)
    with pytest.raises(RuntimeError, match="quota policy stopped"):
        jobs.reserve_quota({"jobType": "metadata_sync"}, 3)
    assert control.updates == []


def test_quota_reservation_is_atomic(monkeypatch: Any) -> None:
    control = FakeControl(100)

    def table() -> FakeControl:
        return control

    monkeypatch.setattr(jobs, "_control_table", table)
    assert jobs.reserve_quota({"jobType": "metadata_sync"}, 3) == 3
    assert control.updates[0]["ConditionExpression"] == (
        "attribute_not_exists(used) OR used <= :remaining"
    )


def test_live_chat_restores_and_persists_s3_checkpoint(monkeypatch: Any) -> None:
    store = FakeS3()
    store.objects[("raw-bucket", "checkpoints/live-chat/video-1.json")] = (
        b'{"status":"running","messageIds":[]}'
    )

    def client(_service: str) -> FakeS3:
        return store

    def no_quota(*_args: object) -> None:
        return None

    def reserve(*_args: object) -> int:
        return 5

    def youtube() -> FakeLiveYouTube:
        return FakeLiveYouTube()

    monkeypatch.setenv("RAW_BUCKET", "raw-bucket")
    monkeypatch.setattr(jobs.boto3, "client", client)
    monkeypatch.setattr(jobs, "_youtube", youtube)
    monkeypatch.setattr(jobs, "_record_quota", no_quota)
    monkeypatch.setattr(jobs, "reserve_quota", reserve)
    monkeypatch.setattr(jobs, "_enqueue_child", no_quota)

    jobs.live_chat_collect(
        {
            "jobId": "job-live",
            "jobType": "live_chat_collect",
            "targetId": "video-1",
            "inputVersion": "v1",
            "inputManifest": {
                "liveChatId": "chat-1",
                "streamStartedAt": "2026-01-01T00:00:00Z",
                "maxPages": 3,
            },
        }
    )
    checkpoint = store.objects[("raw-bucket", "checkpoints/live-chat/video-1.json")]
    assert b"checkpointed" in checkpoint


def test_live_start_quota_is_protected_above_stop_threshold(monkeypatch: Any) -> None:
    control = FakeControl(9900)

    def table() -> FakeControl:
        return control

    monkeypatch.setattr(jobs, "_control_table", table)
    assert (
        jobs.reserve_quota(
            {
                "jobType": "metadata_sync",
                "inputManifest": {"discoverLive": True},
            },
            200,
        )
        == 200
    )
    assert "ConditionExpression" not in control.updates[0]


def test_operations_heartbeat_emits_export_age(monkeypatch: Any) -> None:
    store = FakeS3()
    store.objects[("public-bucket", "data/latest.json")] = b'{"generatedAt":"2026-01-01T00:00:00Z"}'
    metrics: list[tuple[str, int | float]] = []

    def client(_service: str) -> FakeS3:
        return store

    def emit(name: str, value: int | float, _dimensions: dict[str, str]) -> None:
        metrics.append((name, value))

    monkeypatch.setenv("PUBLIC_BUCKET", "public-bucket")
    monkeypatch.delenv("DISTRIBUTION_DOMAIN_NAME", raising=False)
    monkeypatch.setattr(jobs.boto3, "client", client)
    monkeypatch.setattr(jobs, "_emit_metric", emit)

    result = jobs.operations_heartbeat()
    assert result["latestExportAgeHours"] > 0
    assert metrics[0][0] == "LatestExportAgeHours"
