import json
from pathlib import Path

from app.scripts.import_archive_timestamps import build_release


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_build_release_exports_only_approved_public_timestamp_values(tmp_path: Path) -> None:
    """承認済み入力から許可済みの公開タイムスタンプだけを移植することを検証する。"""
    # 1. 初期化
    seed = tmp_path / "seed"
    _write_json(seed / "index.json", {"videos": [{"videoId": "seed"}]})
    _write_json(seed / "search-index.json", {"videos": [{"videoId": "seed"}]})
    for name in ("tag-taxonomy.json", "tag-index.json", "tag-alias-index.json"):
        _write_json(seed / name, {"releaseId": "seed", "generatedAt": "2026-01-01T00:00:00Z"})
    _write_json(seed / "videos" / "seed.json", {"videoId": "seed"})
    manifest = tmp_path / "manifest.json"
    _write_json(
        manifest,
        {
            "generatedAt": "2026-01-01T01:00:00Z",
            "videos": [
                {
                    "videoId": "known",
                    "title": "実動画",
                    "publishedAt": "2026-01-01T00:00:00Z",
                    "duration": "PT1M",
                    "durationSeconds": 60,
                },
                {
                    "videoId": "missing-time",
                    "title": "時刻不足",
                    "publishedAt": "2026-01-01T00:00:00Z",
                    "duration": "PT1M",
                    "durationSeconds": 60,
                },
            ],
        },
    )
    final_root = tmp_path / "finals"
    _write_json(
        final_root / "known" / "final.json",
        {
            "videoId": "known",
            "status": "approved",
            "provenance": {"completedAt": "2026-01-02T00:00:00Z", "models": ["private"]},
            "chapters": [
                {
                    "startSeconds": 12,
                    "publicTitle": "公開章",
                    "confidence": "high",
                    "internalTopic": "非公開",
                    "evidenceRefs": ["private"],
                }
            ],
        },
    )
    _write_json(
        final_root / "missing" / "final.json",
        {
            "videoId": "missing",
            "status": "approved",
            "provenance": {"completedAt": "2026-01-02T00:00:00Z"},
            "chapters": [],
        },
    )
    _write_json(
        final_root / "missing-time" / "final.json",
        {"videoId": "missing-time", "status": "approved", "provenance": {}, "chapters": []},
    )

    # 2. テストの実行
    result = build_release(
        final_root=final_root,
        manifest_path=manifest,
        seed_release=seed,
        output=tmp_path / "output",
        release_id="release",
        generated_at="2026-01-03T00:00:00Z",
    )

    # 3. アサーション
    detail = json.loads((tmp_path / "output" / "videos" / "known.json").read_text(encoding="utf-8"))
    assert result == {
        "releaseId": "release",
        "approvedCount": 3,
        "importedCount": 1,
        "excluded": [
            {"videoId": "missing", "reason": "missing_target_manifest_metadata"},
            {"videoId": "missing-time", "reason": "missing_provenance_completed_at"},
        ],
        "videoCount": 2,
    }
    assert detail["timestamps"] == {
        "status": "generated",
        "source": "get_archives_info_v1",
        "generatedAt": "2026-01-02T00:00:00Z",
        "items": [{"atSec": 12, "label": "公開章", "confidenceLevel": "high"}],
    }
    assert "internalTopic" not in json.dumps(detail, ensure_ascii=False)
    assert (
        json.loads((tmp_path / "output" / "index.json").read_text(encoding="utf-8"))["videos"][1][
            "artifactFlags"
        ]["timestamps"]
        is True
    )
