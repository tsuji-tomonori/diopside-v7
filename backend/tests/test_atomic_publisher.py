import json
from pathlib import Path

import pytest

from app.exporter.publisher import AtomicPublisher, ReleaseRejected


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def candidate(root: Path, release_id: str, *, omit_detail: bool = False) -> Path:
    release = root / release_id
    base = {
        "schemaVersion": "1.0.0",
        "releaseId": release_id,
        "releaseMode": "normal",
        "generatedAt": "2026-01-01T00:00:00Z",
        "layout": "monolithic",
        "normalizationVersion": "test-v1",
        "taxonomyVersion": "test-v1",
        "aliasVersion": "test-v1",
    }
    video = {
        "videoId": "video-1",
        "title": "title",
        "publishedAt": "2026-01-01T00:00:00Z",
        "durationSec": 60,
        "duration": "PT1M",
        "thumbnail": {"url": "https://example.test/thumb.jpg", "width": 640, "height": 360},
        "sourceKind": "youtube_api",
        "metadataStatus": "complete",
        "sourceUpdatedAt": "2026-01-01T00:00:00Z",
        "artifactFlags": {
            "chat": False,
            "comments": False,
            "timestamps": False,
            "wordcloud": False,
        },
        "tagIds": ["tag-1"],
        "provenance": {"titleSource": "youtube", "publishedSource": "youtube"},
        "coverage": {
            "coverageStart": "2026-01-01T00:00:00Z",
            "coverageEnd": "2026-01-01T00:01:00Z",
            "completeFromStart": True,
            "sourceUpdatedAt": "2026-01-01T00:00:00Z",
        },
    }
    write(release / "index.json", {**base, "videos": [video]})
    write(release / "search-index.json", {**base, "videos": [{"videoId": "video-1"}]})
    write(release / "tag-taxonomy.json", {**base, "categories": []})
    write(release / "tag-index.json", {**base, "tags": [{"tagId": "tag-1"}]})
    write(release / "tag-alias-index.json", {**base, "aliases": {}})
    if not omit_detail:
        write(release / "videos" / "video-1.json", {**video, "releaseId": release_id})
    return release


def test_valid_release_switches_latest_atomically(tmp_path: Path) -> None:
    public = tmp_path / "public"
    result = AtomicPublisher(public).publish(candidate(tmp_path / "candidates", "release-a"))

    latest = json.loads((public / "latest.json").read_text())
    assert result.video_count == 1
    assert latest["releaseId"] == "release-a"
    assert (public / "releases" / "release-a" / "index.json").is_file()


def test_invalid_release_does_not_replace_latest(tmp_path: Path) -> None:
    public = tmp_path / "public"
    publisher = AtomicPublisher(public)
    publisher.publish(candidate(tmp_path / "candidates", "release-a"))
    before = (public / "latest.json").read_bytes()

    with pytest.raises(ReleaseRejected, match="missing_artifact"):
        publisher.publish(candidate(tmp_path / "candidates", "release-b", omit_detail=True))

    assert (public / "latest.json").read_bytes() == before
    assert not (public / "releases" / "release-b").exists()
