from __future__ import annotations

import argparse
import json
import shutil
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

NORMALIZATION_VERSION = "unicode-15.1/tokenizer-v1"


def _read_object(path: Path) -> dict[str, Any]:
    value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path}")
    return cast(dict[str, Any], value)


def _read_videos(path: Path) -> dict[str, dict[str, Any]]:
    document = _read_object(path)
    values = document.get("videos")
    if not isinstance(values, list):
        raise ValueError(f"videos array required: {path}")
    videos: dict[str, dict[str, Any]] = {}
    for raw in cast(list[object], values):
        if not isinstance(raw, dict):
            continue
        item = cast(dict[str, Any], raw)
        video_id = item.get("videoId")
        if isinstance(video_id, str) and video_id:
            videos[video_id] = item
    return videos


def _timestamp_items(chapters: object) -> list[dict[str, object]]:
    if not isinstance(chapters, list):
        raise ValueError("approved final.json requires chapters array")
    items: list[dict[str, object]] = []
    for raw in cast(list[object], chapters):
        if not isinstance(raw, dict):
            raise ValueError("chapter must be an object")
        chapter = cast(dict[str, object], raw)
        start = chapter.get("startSeconds")
        title = chapter.get("publicTitle")
        confidence = chapter.get("confidence")
        if (
            isinstance(start, bool)
            or not isinstance(start, int | float)
            or start < 0
            or not isinstance(title, str)
            or not title
            or confidence not in ("high", "medium", "low")
        ):
            raise ValueError("chapter has invalid public timestamp values")
        items.append(
            {
                "atSec": int(start),
                "label": title,
                "confidenceLevel": confidence,
            }
        )
    return items


def _approved_finals(final_root: Path) -> Iterable[dict[str, Any]]:
    for path in sorted(final_root.glob("*/final.json")):
        document = _read_object(path)
        if document.get("status") == "approved":
            yield document


def _index_record(
    manifest: dict[str, Any], timestamp_present: bool, manifest_generated_at: str
) -> dict[str, Any]:
    video_id = manifest["videoId"]
    published_at = manifest["publishedAt"]
    duration_seconds = manifest["durationSeconds"]
    duration = manifest["duration"]
    if not all(
        (
            isinstance(video_id, str),
            isinstance(manifest.get("title"), str),
            isinstance(published_at, str),
            isinstance(duration_seconds, int),
            isinstance(duration, str),
        )
    ):
        raise ValueError(f"manifest metadata is invalid: {video_id}")
    return {
        "videoId": video_id,
        "title": manifest["title"],
        "publishedAt": published_at,
        "duration": duration,
        "durationSec": duration_seconds,
        "thumbnail": {
            "url": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "width": 480,
            "height": 360,
        },
        "sourceKind": "youtube_api",
        "metadataStatus": "complete",
        "sourceUpdatedAt": manifest_generated_at,
        "artifactFlags": {
            "chat": False,
            "comments": False,
            "timestamps": timestamp_present,
            "wordcloudChat": False,
            "wordcloudComments": False,
            "wordcloudBoth": False,
        },
        "tagIds": [],
        "provenance": {
            "titleSource": "target_manifest_v1",
            "publishedSource": "target_manifest_v1",
        },
    }


def _search_record(video: dict[str, Any]) -> dict[str, Any]:
    return {
        "videoId": video["videoId"],
        "titleTokens": [video["title"]],
        "sourceKind": video["sourceKind"],
        "metadataStatus": video["metadataStatus"],
        "publishedAt": video["publishedAt"],
        "publishedDate": video["publishedAt"][:10],
        "durationSec": video["durationSec"],
        "artifactFlags": video["artifactFlags"],
        "tagIds": video["tagIds"],
    }


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_release(
    *,
    final_root: Path,
    manifest_path: Path,
    seed_release: Path,
    output: Path,
    release_id: str,
    generated_at: str,
) -> dict[str, Any]:
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    manifest_document = _read_object(manifest_path)
    manifest_generated_at = manifest_document.get("generatedAt")
    if not isinstance(manifest_generated_at, str):
        raise ValueError(f"generatedAt is required: {manifest_path}")
    manifest_videos = _read_videos(manifest_path)
    seed_index = _read_object(seed_release / "index.json")
    seed_search = _read_object(seed_release / "search-index.json")
    seed_videos = cast(list[dict[str, Any]], seed_index["videos"])
    seed_search_videos = cast(list[dict[str, Any]], seed_search["videos"])
    shutil.copytree(seed_release, output)
    for path in (output / "videos").glob("*.json"):
        detail = _read_object(path)
        wordcloud = detail.get("wordcloud")
        if isinstance(wordcloud, dict):
            wordcloud_document = cast(dict[str, Any], wordcloud)
            for field in ("svgPath", "jsonPath"):
                value = wordcloud_document.get(field)
                if isinstance(value, str):
                    wordcloud_document[field] = value.replace(
                        f"releases/{seed_release.name}/", f"releases/{release_id}/"
                    )
            _write_json(path, detail)

    imported: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []
    for final in _approved_finals(final_root):
        video_id = final.get("videoId")
        if not isinstance(video_id, str) or not video_id:
            raise ValueError("approved final.json requires videoId")
        manifest = manifest_videos.get(video_id)
        if manifest is None:
            excluded.append({"videoId": video_id, "reason": "missing_target_manifest_metadata"})
            continue
        provenance = final.get("provenance")
        if not isinstance(provenance, dict):
            excluded.append({"videoId": video_id, "reason": "missing_provenance_completed_at"})
            continue
        provenance_document = cast(dict[str, Any], provenance)
        completed_at = provenance_document.get("completedAt")
        if not isinstance(completed_at, str):
            excluded.append({"videoId": video_id, "reason": "missing_provenance_completed_at"})
            continue
        video = _index_record(
            manifest, timestamp_present=True, manifest_generated_at=manifest_generated_at
        )
        detail = dict(video)
        detail["timestamps"] = {
            "status": "generated",
            "source": "get_archives_info_v1",
            "generatedAt": completed_at,
            "items": _timestamp_items(final.get("chapters")),
        }
        _write_json(output / "videos" / f"{video_id}.json", detail)
        imported.append(video)

    videos = [*seed_videos, *sorted(imported, key=lambda item: item["videoId"])]
    search_videos = [
        *seed_search_videos,
        *[_search_record(item) for item in sorted(imported, key=lambda item: item["videoId"])],
    ]
    for name in ("tag-taxonomy.json", "tag-index.json", "tag-alias-index.json"):
        document = _read_object(output / name)
        document.update({"releaseId": release_id, "generatedAt": generated_at})
        _write_json(output / name, document)
    index = {
        **seed_index,
        "releaseId": release_id,
        "generatedAt": generated_at,
        "normalizationVersion": NORMALIZATION_VERSION,
        "videos": videos,
    }
    search = {
        **seed_search,
        "releaseId": release_id,
        "generatedAt": generated_at,
        "normalizationVersion": NORMALIZATION_VERSION,
        "videos": search_videos,
    }
    _write_json(output / "index.json", index)
    _write_json(output / "search-index.json", search)
    return {
        "releaseId": release_id,
        "approvedCount": len(imported) + len(excluded),
        "importedCount": len(imported),
        "excluded": excluded,
        "videoCount": len(videos),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="承認済みタイムスタンプを公開releaseへ移植する")
    parser.add_argument("--final-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--seed-release", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--latest-output", type=Path)
    args = parser.parse_args()
    result = build_release(
        final_root=args.final_root,
        manifest_path=args.manifest,
        seed_release=args.seed_release,
        output=args.output,
        release_id=args.release_id,
        generated_at=args.generated_at,
    )
    _write_json(args.report, result)
    if args.latest_output:
        _write_json(
            args.latest_output,
            {
                "schemaVersion": "1.0.0",
                "releaseId": args.release_id,
                "generatedAt": args.generated_at,
                "releaseMode": "normal",
                "normalizationVersion": NORMALIZATION_VERSION,
                "indexPath": f"data/releases/{args.release_id}/index.json",
                "searchIndexPath": f"data/releases/{args.release_id}/search-index.json",
                "tagTaxonomyPath": f"data/releases/{args.release_id}/tag-taxonomy.json",
                "tagIndexPath": f"data/releases/{args.release_id}/tag-index.json",
                "tagAliasIndexPath": f"data/releases/{args.release_id}/tag-alias-index.json",
            },
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
