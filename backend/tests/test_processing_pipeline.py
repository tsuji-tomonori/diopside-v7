from datetime import UTC, datetime

import pytest

from app.processing.pipeline import (
    Coverage,
    ProcessingError,
    aggregate_events,
    assert_public,
    author_token,
    classify_video_state,
    normalize_chat_message,
    normalize_metadata,
    normalize_text,
    timestamp_candidates,
    wordcloud_artifact,
)


def test_metadata_preserves_missing_values_and_separates_source_tags() -> None:
    metadata = normalize_metadata(
        {
            "id": "abcdefghijk",
            "etag": "etag",
            "snippet": {
                "channelId": "channel",
                "title": "title",
                "tags": ["source-tag"],
                "liveBroadcastContent": "none",
            },
            "contentDetails": {"duration": "PT1H"},
            "status": {"privacyStatus": "public", "embeddable": True},
        },
        "2026-01-01T00:00:00Z",
    )
    assert metadata["sourceTags"] == ["source-tag"]
    assert "viewCount" not in metadata
    assert "tagAssignments" not in metadata
    assert classify_video_state(metadata) == "archive"


def test_chat_normalization_is_idempotent_and_video_scoped() -> None:
    item = {
        "id": "message-1",
        "snippet": {
            "publishedAt": "2026-01-01T00:01:00Z",
            "type": "textMessageEvent",
            "displayMessage": " hello https://example.test ",
        },
        "authorDetails": {"channelId": "author"},
    }
    started = datetime(2026, 1, 1, tzinfo=UTC)
    first = normalize_chat_message(item, "video-one", started, b"secret")
    second = normalize_chat_message(item, "video-one", started, b"secret")
    assert first == second
    assert first["relativeSec"] == 60
    assert first["text"] == "hello"
    assert author_token(b"secret", "video-one", "author") != author_token(
        b"secret", "video-two", "author"
    )


def test_public_aggregate_excludes_private_fields() -> None:
    coverage = Coverage(
        "2026-01-01T00:00:00Z",
        "2026-01-01T01:00:00Z",
        True,
        "2026-01-01T01:01:00Z",
    )
    aggregate = aggregate_events(
        [
            {
                "text": "白雪巴 配信 白雪巴",
                "authorDedupToken": "private-token",
                "relativeSec": 1,
                "eventAt": "2026-01-01T00:00:01Z",
            }
        ],
        "chat",
        coverage,
        "2026-01-01T01:02:00Z",
    )
    assert aggregate["totalCount"] == 1
    assert aggregate["uniqueAuthorsApprox"] == 1
    assert "authorDedupToken" not in str(aggregate)


def test_wordcloud_has_safe_svg_or_honest_empty_state() -> None:
    coverage = Coverage("a", "b", False, "c")
    empty, svg = wordcloud_artifact(
        "abcdefghijk", "chat", {"topTerms": []}, coverage, "2026-01-01T00:00:00Z"
    )
    assert empty["notGeneratedReason"] == "insufficient_terms"
    assert svg is None

    generated, svg = wordcloud_artifact(
        "abcdefghijk",
        "chat",
        {
            "topTerms": [
                {"term": "<script>", "count": 3},
                {"term": "配信", "count": 2},
                {"term": "歌枠", "count": 1},
            ]
        },
        coverage,
        "2026-01-01T00:00:00Z",
    )
    assert generated["status"] == "generated"
    assert svg is not None and "&lt;script&gt;" in svg
    assert "<script>" not in svg
    assert "onload=" not in svg


def test_private_field_guard_is_recursive() -> None:
    with pytest.raises(ProcessingError, match="private field"):
        assert_public({"nested": [{"authorChannelId": "secret"}]})


def test_text_normalization_is_deterministic() -> None:
    assert normalize_text("\uff21\uff22\uff23\r\nhttps://example.test\x00") == "ABC"


def test_timestamp_candidates_are_deterministic_and_within_duration() -> None:
    coverage = Coverage("a", "b", True, "c")
    aggregate = {
        "timeline": [
            {"at": 120, "count": 5},
            {"at": 60, "count": 10},
            {"at": 999, "count": 100},
        ]
    }
    first = timestamp_candidates("abcdefghijk", aggregate, 180, coverage, "now")
    second = timestamp_candidates("abcdefghijk", aggregate, 180, coverage, "now")
    assert first == second
    assert [item["atSec"] for item in first["items"]] == [60, 120]
    assert first["items"][0]["confidence"] == 1.0
    assert first["items"][0]["evidenceType"] == "chat_volume"
