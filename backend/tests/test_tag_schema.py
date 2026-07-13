from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from app.tagging.pipeline import migrate_snapshots
from app.tagging.schema import TagSchemaError, validate_tag_document


def _assignment(category: str, subcategory: str, tag: str) -> dict[str, str]:
    return {
        "categoryId": category,
        "category": category,
        "subcategoryId": subcategory,
        "subcategory": subcategory,
        "tag": tag,
        "reason": "fixture reason",
        "source": "fixture.json",
        "evidence": tag,
        "confidence": "high",
    }


def _snapshot() -> dict[str, Any]:
    return migrate_snapshots(
        [
            {
                "videos": [
                    {
                        "videoId": "abcdefghijk",
                        "title": "fixture",
                        "publishedAt": "2026-07-13T00:00:00Z",
                        "channelTitle": "channel",
                        "duration": "PT1M",
                        "tags": [
                            _assignment("content", "primary", "企画"),
                            _assignment("format", "media", "動画"),
                            _assignment("people", "channel", "channel"),
                        ],
                    }
                ]
            }
        ],
        {"exactAliases": []},
        taxonomy_version="3",
        alias_version="3",
        algorithm_version="test",
        scope_decision_version="test",
        generated_at="2026-07-13T00:00:00Z",
    )


def test_snapshot_schema_accepts_migration_output_and_rejects_invalid_fixture() -> None:
    """snapshot schemaが移行出力を受理し、不正fixtureを拒否することを検証する。"""
    snapshot = _snapshot()
    validate_tag_document(snapshot, "snapshot")

    invalid = copy.deepcopy(snapshot)
    invalid["videos"][0]["tagAssignments"][0]["confidence"] = "low"
    with pytest.raises(TagSchemaError, match="confidence"):
        validate_tag_document(invalid, "snapshot")


def test_correction_schema_accepts_ledger_and_rejects_unknown_operation() -> None:
    """補正schemaがledgerを受理し、未知の操作を拒否することを検証する。"""
    path = Path(__file__).resolve().parents[1] / "data" / "tag-corrections-v3.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    validate_tag_document(ledger, "correction")

    invalid = copy.deepcopy(ledger)
    invalid["assignmentCorrections"][0]["operation"] = "upsert"
    with pytest.raises(TagSchemaError, match="assignmentCorrections"):
        validate_tag_document(invalid, "correction")


def test_schema_resolver_rejects_unknown_version() -> None:
    """schema解決処理が未知のversionを拒否することを検証する。"""
    with pytest.raises(TagSchemaError, match="unsupported snapshot schemaVersion"):
        validate_tag_document({"schemaVersion": "4.0.0"}, "snapshot")


def test_usage_decision_schema_requires_default_exclusion_and_valid_gates() -> None:
    """利用判断schemaが既定除外と有効なgateを要求することを検証する。"""
    path = Path(__file__).resolve().parents[1] / "data" / "usage-decisions-v1.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    validate_tag_document(ledger, "usage")

    invalid = copy.deepcopy(ledger)
    invalid["defaultDecision"] = "allow"
    with pytest.raises(TagSchemaError, match="defaultDecision"):
        validate_tag_document(invalid, "usage")

    duplicate = copy.deepcopy(ledger)
    duplicate["decisions"].append(copy.deepcopy(duplicate["decisions"][0]))
    with pytest.raises(TagSchemaError, match="sourceKind values must be unique"):
        validate_tag_document(duplicate, "usage")
