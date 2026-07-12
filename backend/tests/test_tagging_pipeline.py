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
