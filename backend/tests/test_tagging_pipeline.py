from typing import Any, cast

import pytest

from app.tagging.pipeline import TaggingError, migrate_snapshots, normalize_match, stable_tag_id


def assignment(category: str, subcategory: str, tag: str) -> dict[str, str]:
    return {
        "categoryId": category,
        "category": category,
        "subcategoryId": subcategory,
        "subcategory": subcategory,
        "tag": tag,
        "reason": "fixture",
        "source": "fixture.json",
        "evidence": tag,
        "confidence": "high",
    }


def video(tags: list[dict[str, str]]) -> dict[str, object]:
    return {
        "videoId": "video-1",
        "title": "title",
        "publishedAt": "2026-01-01T00:00:00Z",
        "channelTitle": "channel",
        "duration": "PT1H",
        "tags": tags,
    }


def migrate(tags: list[dict[str, str]]) -> dict[str, object]:
    return migrate_snapshots(
        [{"videos": [video(tags)]}],
        {
            "exactAliases": [
                {"field": "works.gameTitle", "canonical": "Minecraft", "aliases": ["マイクラ"]}
            ]
        },
        taxonomy_version="2",
        alias_version="2",
        algorithm_version="test",
        scope_decision_version="test",
        generated_at="2026-01-01T00:00:00Z",
    )


def required_tags() -> list[dict[str, str]]:
    return [
        assignment("content", "primary", "ゲーム"),
        assignment("format", "media", "配信"),
        assignment("people", "channel", "channel"),
    ]


def test_stable_id_is_axis_aware_and_normalized() -> None:
    assert normalize_match(" \uff03Minecraft  ") == "minecraft"
    assert stable_tag_id("works", "gameTitle", "Minecraft") == stable_tag_id(
        "works", "gameTitle", "\uff2d\uff49\uff4e\uff45\uff43\uff52\uff41\uff46\uff54"
    )
    assert stable_tag_id("works", "gameTitle", "ライブ") != stable_tag_id(
        "format", "media", "ライブ"
    )


def test_alias_is_canonicalized_before_id_assignment() -> None:
    snapshot = migrate([*required_tags(), assignment("works", "gameTitle", "マイクラ")])
    definitions = snapshot["tagDefinitions"]
    assert isinstance(definitions, list)
    typed_definitions = cast(list[dict[str, Any]], definitions)
    assert any(item["canonicalName"] == "Minecraft" for item in typed_definitions)


def test_missing_singleton_is_rejected() -> None:
    with pytest.raises(TaggingError, match=r"format\.media"):
        tags = required_tags()
        migrate([tags[0], tags[2]])


def test_review_placeholder_is_rejected() -> None:
    with pytest.raises(TaggingError, match="blocked assignment"):
        migrate([*required_tags(), assignment("works", "gameTitle", "要確認")])


def test_channel_identity_correction_unifies_performer_alias() -> None:
    snapshot = migrate_snapshots(
        [
            {
                "videos": [
                    video(
                        [
                            *required_tags(),
                            assignment("people", "performer", "Kotoka Torahime"),
                        ]
                    )
                ]
            }
        ],
        {"exactAliases": []},
        correction_document={
            "correctionVersion": "v1",
            "records": [
                {
                    "field": "people.performer",
                    "canonical": "虎姫コトカ",
                    "aliases": ["Kotoka Torahime"],
                    "evidenceType": "channel_id_identity",
                    "channelId": "UCggO2c1unS-oLwTLT0ICywg",
                }
            ],
        },
        taxonomy_version="2",
        alias_version="2",
        algorithm_version="test",
        scope_decision_version="test",
        generated_at="2026-01-01T00:00:00Z",
    )
    definitions = cast(list[dict[str, Any]], snapshot["tagDefinitions"])
    assert any(item["canonicalName"] == "虎姫コトカ" for item in definitions)
    assert snapshot["correctionVersion"] == "v1"


def test_received_archive_source_is_rewritten_to_existing_file() -> None:
    tags = required_tags()
    tags[1]["source"] = "archive_index"
    snapshot = migrate(tags)
    videos = cast(list[dict[str, Any]], snapshot["videos"])
    assignments = cast(list[dict[str, Any]], videos[0]["tagAssignments"])
    media = next(item for item in assignments if item["subcategoryId"] == "media")
    assert media["source"] == "archive_index.p0.json"
