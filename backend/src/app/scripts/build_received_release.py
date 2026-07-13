from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

from app.exporter.publisher import NormalReleaseBuilder
from app.tagging.pipeline import migrate_snapshots, normalize_match, stable_tag_id
from app.tagging.schema import validate_tag_document


def _archive_object(archive: ZipFile, name: str) -> dict[str, Any]:
    value = cast(object, json.loads(archive.read(name)))
    if not isinstance(value, dict):
        raise ValueError(f"{name} must contain a JSON object")
    return cast(dict[str, Any], value)


def _file_object(path: Path) -> dict[str, Any]:
    value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return cast(dict[str, Any], value)


def _videos(document: dict[str, Any]) -> list[dict[str, Any]]:
    values = document.get("videos", [])
    if not isinstance(values, list):
        raise ValueError("videos must be an array")
    return [
        cast(dict[str, Any], item) for item in cast(list[object], values) if isinstance(item, dict)
    ]


def _public_taxonomy(snapshot: dict[str, Any]) -> dict[str, Any]:
    hierarchy: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    category_labels: dict[str, str] = {}
    for video in _videos(snapshot):
        assignments = video.get("tagAssignments", [])
        if not isinstance(assignments, list):
            continue
        for raw in cast(list[object], assignments):
            if not isinstance(raw, dict):
                continue
            item = cast(dict[str, Any], raw)
            category = str(item["categoryId"])
            subcategory = str(item["subcategoryId"])
            category_labels[category] = str(item["category"])
            node = hierarchy[category].setdefault(
                subcategory,
                {
                    "subcategoryId": subcategory,
                    "label": str(item["subcategory"]),
                    "tagIds": set(),
                },
            )
            cast(set[str], node["tagIds"]).add(str(item["tagId"]))
    return {
        "categories": [
            {
                "categoryId": category,
                "label": category_labels[category],
                "subcategories": [
                    {**node, "tagIds": sorted(cast(set[str], node["tagIds"]))}
                    for _, node in sorted(hierarchy[category].items())
                ],
            }
            for category in sorted(hierarchy)
        ]
    }


def _public_aliases(aliases: dict[str, Any], corrections: dict[str, Any]) -> dict[str, Any]:
    candidates: dict[str, set[str]] = defaultdict(set)
    records: list[dict[str, Any]] = []
    for key in ("exactAliases",):
        values = aliases.get(key, [])
        if isinstance(values, list):
            records.extend(
                cast(dict[str, Any], item)
                for item in cast(list[object], values)
                if isinstance(item, dict)
            )
    correction_values = corrections.get("records", [])
    if isinstance(correction_values, list):
        records.extend(
            cast(dict[str, Any], item)
            for item in cast(list[object], correction_values)
            if isinstance(item, dict)
        )
    for record in records:
        field = record.get("field")
        canonical = record.get("canonical")
        if not isinstance(field, str) or not isinstance(canonical, str) or "." not in field:
            continue
        category, subcategory = field.split(".", 1)
        tag_id = stable_tag_id(category, subcategory, canonical)
        values = [canonical, *cast(list[object], record.get("aliases", []))]
        for value in values:
            if isinstance(value, str):
                candidates[normalize_match(value)].add(tag_id)
    return {
        "aliases": {
            alias: next(iter(tag_ids))
            for alias, tag_ids in sorted(candidates.items())
            if len(tag_ids) == 1
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="受領タグ証拠から正規候補を構築する")
    parser.add_argument("--tags-zip", type=Path, required=True)
    parser.add_argument("--corrections", type=Path, required=True)
    parser.add_argument("--usage-decisions", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    corrections = _file_object(args.corrections)
    validate_tag_document(corrections, "correction")
    usage_decisions = _file_object(args.usage_decisions)
    validate_tag_document(usage_decisions, "usage")
    with ZipFile(args.tags_zip) as archive:
        own = _archive_object(archive, "tags/video_tags_v2.json")
        external = _archive_object(archive, "tags/collaboration_video_tags_v2.json")
        aliases = _archive_object(archive, "tags/tag_aliases_v2.json")
    snapshot = migrate_snapshots(
        [own, external],
        aliases,
        correction_document=corrections,
        taxonomy_version="2.0.0",
        alias_version="2.0.0",
        algorithm_version="tag-migration-v1",
        scope_decision_version="20260711-v1",
        generated_at="2026-07-13T00:00:00Z",
    )
    own_ids = {str(item.get("videoId")) for item in _videos(own)}
    validate_tag_document(snapshot, "snapshot")
    metadata: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for item in [*_videos(own), *_videos(external)]:
        video_id = str(item.get("videoId", ""))
        if item.get("metadataStatus") == "Wiki情報のみ":
            excluded.append(
                {
                    "videoId": video_id,
                    "reason": "wiki_only_missing_required_youtube_metadata",
                }
            )
            continue
        metadata.append(
            {
                "videoId": video_id,
                "channelId": "official" if video_id in own_ids else "external",
                "title": item.get("title"),
                "publishedAt": item.get("publishedAt"),
                "duration": item.get("duration"),
                "thumbnail": {
                    "url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    "width": 480,
                    "height": 360,
                },
                "fetchedAt": "2026-07-13T00:00:00Z",
            }
        )
    result = NormalReleaseBuilder().build(
        args.output,
        release_id=args.release_id,
        metadata=metadata,
        tag_snapshot=snapshot,
        taxonomy=_public_taxonomy(snapshot),
        aliases=_public_aliases(aliases, corrections),
        official_channel_id="official",
        generated_at="2026-07-13T00:00:00Z",
    )
    report = {
        "schemaVersion": "1.0.0",
        "releaseId": result.release_id,
        "sourceVideoCount": snapshot["videoCount"],
        "eligibleVideoCount": result.video_count,
        "excludedVideoCount": len(excluded),
        "populationAccountedFor": result.video_count + len(excluded),
        "assignmentCount": snapshot["assignmentCount"],
        "reviewAssignmentCount": snapshot["reviewAssignmentCount"],
        "correctionVersion": snapshot["correctionVersion"],
        "usageDecisionVersion": usage_decisions["decisionVersion"],
        "releaseFingerprint": hashlib.sha256(
            json.dumps(
                result.artifact_hashes,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest(),
        "excluded": excluded,
        "reviewAssignments": snapshot["reviewAssignments"],
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
