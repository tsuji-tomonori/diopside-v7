from typing import Any, cast

import pytest

from app.runtime import jobs


class FakeYouTube:
    def __enter__(self) -> "FakeYouTube":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def channel(self, channel_id: str) -> dict[str, Any]:
        assert channel_id == "channel-1"
        return {"contentDetails": {"relatedPlaylists": {"uploads": "playlist-1"}}}

    def uploads(
        self, playlist_id: str, *, max_pages: int | None = None
    ) -> list[dict[str, Any]]:
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

    def put_object(self, **kwargs: object) -> object:
        self.puts.append(kwargs)
        return {}


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
