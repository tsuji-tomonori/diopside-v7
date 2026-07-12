import json
from pathlib import Path

import pytest

from app.exporter.publisher import (
    AtomicPublisher,
    CompliancePurgeBuilder,
    ReleaseRejected,
    sha256,
)


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
            "wordcloudChat": False,
            "wordcloudComments": False,
            "wordcloudBoth": False,
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
    write(
        release / "search-index.json",
        {
            **base,
            "videos": [
                {"videoId": "video-1", "artifactFlags": video["artifactFlags"]}
            ],
        },
    )
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


def test_release_with_private_field_is_rejected(tmp_path: Path) -> None:
    release = candidate(tmp_path / "candidates", "release-private")
    detail_path = release / "videos" / "video-1.json"
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    detail["messageText"] = "must stay private"
    write(detail_path, detail)

    with pytest.raises(ReleaseRejected, match="private_field"):
        AtomicPublisher(tmp_path / "public").publish(release)


def test_release_with_unsafe_svg_is_rejected(tmp_path: Path) -> None:
    release = candidate(tmp_path / "candidates", "release-svg")
    for relative in ("index.json", "search-index.json"):
        path = release / relative
        document = json.loads(path.read_text(encoding="utf-8"))
        document["videos"][0]["artifactFlags"]["wordcloudChat"] = True
        write(path, document)
    detail_path = release / "videos" / "video-1.json"
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    detail["artifactFlags"]["wordcloudChat"] = True
    write(detail_path, detail)
    write(
        release / "wordcloud" / "video-1-chat.json",
        {"releaseId": "release-svg", "status": "generated"},
    )
    svg = release / "wordcloud" / "video-1-chat.svg"
    svg.write_text("<svg xmlns='http://www.w3.org/2000/svg'><script/></svg>", encoding="utf-8")

    with pytest.raises(ReleaseRejected, match="unsafe_svg"):
        AtomicPublisher(tmp_path / "public").publish(release)


def test_compliance_purge_requires_current_base_and_removes_tags(tmp_path: Path) -> None:
    public = tmp_path / "public"
    publisher = AtomicPublisher(public)
    publisher.publish(candidate(tmp_path / "candidates", "release-base"))
    latest = json.loads((public / "latest.json").read_text(encoding="utf-8"))

    purge = candidate(tmp_path / "candidates", "release-purge")
    for name in ("tag-taxonomy.json", "tag-index.json", "tag-alias-index.json"):
        (purge / name).unlink()
    for relative in ("index.json", "search-index.json"):
        path = purge / relative
        document = json.loads(path.read_text(encoding="utf-8"))
        document["releaseMode"] = "compliance_purge"
        document["purgeBaseReleaseId"] = "release-base"
        document["purgeBaseManifestSha256"] = sha256(latest)
        document["purgeTrigger"] = "deletion:test"
        document.pop("taxonomyVersion", None)
        document.pop("aliasVersion", None)
        document["videos"][0].pop("tagIds", None)
        write(path, document)
    detail_path = purge / "videos" / "video-1.json"
    detail = json.loads(detail_path.read_text(encoding="utf-8"))
    detail.pop("tagIds", None)
    write(detail_path, detail)

    publisher.publish(purge)
    published = json.loads((public / "latest.json").read_text(encoding="utf-8"))
    assert published["releaseMode"] == "compliance_purge"
    assert "tagIndexPath" not in published


def test_purge_builder_removes_requested_video_and_all_derived_data(tmp_path: Path) -> None:
    public = tmp_path / "public"
    publisher = AtomicPublisher(public)
    publisher.publish(candidate(tmp_path / "candidates", "release-base"))
    latest = json.loads((public / "latest.json").read_text(encoding="utf-8"))
    output = tmp_path / "candidates" / "release-built-purge"

    result = CompliancePurgeBuilder().build(
        public / "releases" / "release-base",
        output,
        release_id="release-built-purge",
        latest_document=latest,
        excluded_video_ids={"video-1"},
        trigger="deletion:video-1",
        generated_at="2026-01-02T00:00:00Z",
    )

    assert result.video_count == 0
    assert not (output / "tag-index.json").exists()
    assert not (output / "videos" / "video-1.json").exists()
    publisher.publish(output)
    published = json.loads((public / "latest.json").read_text(encoding="utf-8"))
    assert published["releaseId"] == "release-built-purge"
