from typing import Any, cast

from app.runtime import jobs


class FakeYouTube:
    def __enter__(self) -> "FakeYouTube":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def channel(self, channel_id: str) -> dict[str, Any]:
        assert channel_id == "channel-1"
        return {"contentDetails": {"relatedPlaylists": {"uploads": "playlist-1"}}}

    def uploads(self, playlist_id: str) -> list[dict[str, Any]]:
        assert playlist_id == "playlist-1"
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


def test_metadata_sync_collects_and_writes_raw_snapshot(monkeypatch: Any) -> None:
    store = FakeS3()

    def client(_service: str) -> FakeS3:
        return store

    monkeypatch.setenv("RAW_BUCKET", "raw-bucket")
    monkeypatch.setattr(jobs, "_youtube", lambda: FakeYouTube())
    monkeypatch.setattr(jobs.boto3, "client", client)

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
