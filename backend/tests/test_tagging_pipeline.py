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
    """安定IDが軸を区別し、正規化値から生成されることを検証する。"""
    # 1. 初期化
    full_width_minecraft = "\uff2d\uff49\uff4e\uff45\uff43\uff52\uff41\uff46\uff54"

    # 2. テストの実行
    normalized = normalize_match(" \uff03Minecraft  ")
    canonical_id = stable_tag_id("works", "gameTitle", "Minecraft")
    full_width_id = stable_tag_id("works", "gameTitle", full_width_minecraft)
    work_id = stable_tag_id("works", "gameTitle", "ライブ")
    format_id = stable_tag_id("format", "media", "ライブ")

    # 3. アサーション
    assert normalized == "minecraft"
    assert canonical_id == full_width_id
    assert work_id != format_id


def test_alias_is_canonicalized_before_id_assignment() -> None:
    """別名をID付与前に正規化することを検証する。"""
    # 1. 初期化
    tags = [*required_tags(), assignment("works", "gameTitle", "マイクラ")]

    # 2. テストの実行
    snapshot = migrate(tags)
    definitions = snapshot["tagDefinitions"]
    assert isinstance(definitions, list)
    typed_definitions = cast(list[dict[str, Any]], definitions)

    # 3. アサーション
    assert any(item["canonicalName"] == "Minecraft" for item in typed_definitions)


def test_missing_singleton_is_rejected() -> None:
    """必須singletonタグの欠落を拒否することを検証する。"""
    # 1. 初期化
    tags = required_tags()

    # 2. テストの実行
    with pytest.raises(TaggingError) as error:
        migrate([tags[0], tags[2]])

    # 3. アサーション
    assert "format.media" in str(error.value)


def test_review_placeholder_is_rejected() -> None:
    """レビュー用placeholderを公開タグとして拒否することを検証する。"""
    # 1. 初期化
    tags = [*required_tags(), assignment("works", "gameTitle", "要確認")]

    # 2. テストの実行
    with pytest.raises(TaggingError) as error:
        migrate(tags)

    # 3. アサーション
    assert "blocked assignment" in str(error.value)


def test_channel_identity_correction_unifies_performer_alias() -> None:
    """チャンネル同一性補正が出演者の別名を統合することを検証する。"""
    # 1. 初期化
    snapshots = [
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
    ]
    correction = {
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
    }

    # 2. テストの実行
    snapshot = migrate_snapshots(
        snapshots,
        {"exactAliases": []},
        correction_document=correction,
        taxonomy_version="2",
        alias_version="2",
        algorithm_version="test",
        scope_decision_version="test",
        generated_at="2026-01-01T00:00:00Z",
    )
    definitions = cast(list[dict[str, Any]], snapshot["tagDefinitions"])

    # 3. アサーション
    assert any(item["canonicalName"] == "虎姫コトカ" for item in definitions)
    assert snapshot["correctionVersion"] == "v1"


def test_received_archive_source_is_rewritten_to_existing_file() -> None:
    """受領archiveのsourceを実在ファイルへ書き換えることを検証する。"""
    # 1. 初期化
    tags = required_tags()
    tags[1]["source"] = "archive_index"

    # 2. テストの実行
    snapshot = migrate(tags)
    videos = cast(list[dict[str, Any]], snapshot["videos"])
    assignments = cast(list[dict[str, Any]], videos[0]["tagAssignments"])
    media = next(item for item in assignments if item["subcategoryId"] == "media")

    # 3. アサーション
    assert media["source"] == "archive_index.p0.json"


def test_migrate_snapshots_applies_evidence_backed_assignment_correction() -> None:
    """snapshot移行で証拠に基づく割り当て補正を適用することを検証する。"""
    # 1. 初期化
    snapshot = {
        "videos": [
            {
                "videoId": "corrected-video",
                "title": "Guest appears in title",
                "tags": [
                    {
                        "categoryId": "content",
                        "category": "内容",
                        "subcategoryId": "primary",
                        "subcategory": "主ジャンル",
                        "tag": "雑談",
                        "reason": "title classification",
                        "source": "metadata.title",
                        "evidence": "Guest appears in title",
                        "confidence": "high",
                    },
                    {
                        "categoryId": "format",
                        "category": "公開形式",
                        "subcategoryId": "media",
                        "subcategory": "動画形式",
                        "tag": "動画",
                        "reason": "metadata classification",
                        "source": "metadata",
                        "evidence": "PT1M",
                        "confidence": "high",
                    },
                    {
                        "categoryId": "people",
                        "category": "人物・グループ",
                        "subcategoryId": "channel",
                        "subcategory": "公開チャンネル",
                        "tag": "Channel",
                        "reason": "metadata channel",
                        "source": "metadata.channel_title",
                        "evidence": "Channel",
                        "confidence": "high",
                    },
                ],
            }
        ]
    }
    correction = {
        "correctionVersion": "test-v1",
        "records": [],
        "assignmentCorrections": [
            {
                "operation": "add",
                "videoId": "corrected-video",
                "evidenceType": "metadata_title",
                "assignment": {
                    "categoryId": "people",
                    "category": "人物・グループ",
                    "subcategoryId": "performer",
                    "subcategory": "出演者",
                    "tag": "Guest",
                    "reason": "guest named in title",
                    "source": "metadata.title / correction_ledger",
                    "evidence": "Guest",
                    "confidence": "high",
                },
            }
        ],
    }

    # 2. テストの実行
    result = migrate_snapshots(
        [snapshot],
        {"exactAliases": []},
        correction_document=correction,
        taxonomy_version="test",
        alias_version="test",
        algorithm_version="test",
        scope_decision_version="test",
        generated_at="2026-07-13T00:00:00Z",
    )
    assignments = result["videos"][0]["tagAssignments"]

    # 3. アサーション
    assert any(item["tag"] == "Guest" for item in assignments)
    assert result["assignmentCount"] == 4


def test_migrate_snapshots_replaces_and_quarantines_assignments() -> None:
    """snapshot移行が割り当てを置換・隔離することを検証する。"""
    # 1. 初期化
    snapshots = [
        {
            "videos": [
                video(
                    [
                        *required_tags(),
                        assignment("program", "event", "にじさんじ麻雀杯"),
                        assignment("works", "gameTitle", "麻雀"),
                    ]
                )
            ]
        }
    ]
    correction = {
        "correctionVersion": "test-v2",
        "records": [],
        "assignmentCorrections": [
            {
                "operation": "replace",
                "videoId": "video-1",
                "evidenceType": "published_at_event_date",
                "match": {
                    "categoryId": "program",
                    "subcategoryId": "event",
                    "tag": "にじさんじ麻雀杯",
                },
                "assignment": assignment("program", "event", "にじさんじ麻雀杯2023"),
            },
            {
                "operation": "review",
                "videoId": "video-1",
                "evidenceType": "insufficient_specificity",
                "match": {
                    "categoryId": "works",
                    "subcategoryId": "gameTitle",
                    "tag": "麻雀",
                },
                "reviewReason": "A game product cannot be identified from title metadata",
            },
        ],
    }

    # 2. テストの実行
    result = migrate_snapshots(
        snapshots,
        {"exactAliases": []},
        correction_document=correction,
        taxonomy_version="test",
        alias_version="test",
        algorithm_version="test",
        scope_decision_version="test",
        generated_at="2026-07-13T00:00:00Z",
    )
    assignments = cast(list[dict[str, Any]], result["videos"][0]["tagAssignments"])

    # 3. アサーション
    assert any(item["tag"] == "にじさんじ麻雀杯2023" for item in assignments)
    assert not any(item["tag"] == "麻雀" for item in assignments)
    assert result["reviewAssignmentCount"] == 1
    assert result["reviewAssignments"][0]["tag"] == "麻雀"
