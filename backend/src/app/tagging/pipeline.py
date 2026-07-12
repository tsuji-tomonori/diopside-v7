from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final, cast

BLOCKED_VALUES: Final = frozenset({"その他", "不明", "要確認", "未分類・要レビュー"})
SINGLETON_FIELDS: Final = frozenset({"content.primary", "format.media", "people.channel"})
SOURCE_REWRITES: Final = {"archive_index": "archive_index.p0.json"}


class TaggingError(ValueError):
    pass


@dataclass(frozen=True)
class CanonicalTag:
    tag_id: str
    category_id: str
    subcategory_id: str
    canonical_name: str
    display_name: str

    def public_dict(self, count: int, video_ids: list[str]) -> dict[str, Any]:
        return {
            "tagId": self.tag_id,
            "categoryId": self.category_id,
            "subcategoryId": self.subcategory_id,
            "canonicalName": self.canonical_name,
            "displayName": self.display_name,
            "status": "active",
            "introducedInVersion": "3.0.0",
            "count": count,
            "videoIds": video_ids,
        }


def normalize_match(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.removeprefix("#").casefold()


def stable_tag_id(category_id: str, subcategory_id: str, canonical_name: str) -> str:
    identity = f"{category_id}\0{subcategory_id}\0{normalize_match(canonical_name)}"
    digest = hashlib.sha256(identity.encode()).hexdigest()[:20]
    return f"tag_{digest}"


class AliasResolver:
    def __init__(self, alias_document: dict[str, Any]) -> None:
        self._aliases: dict[tuple[str, str], str] = {}
        aliases = alias_document.get("exactAliases", [])
        if not isinstance(aliases, list):
            raise TaggingError("exactAliases must be an array")
        for raw in cast(list[object], aliases):
            item = _object(raw)
            field = _string(item, "field")
            canonical = _string(item, "canonical")
            self._register(field, canonical, canonical)
            values = item.get("aliases", [])
            if not isinstance(values, list):
                raise TaggingError("aliases must be an array")
            for value in cast(list[object], values):
                if isinstance(value, str):
                    self._register(field, value, canonical)

    def _register(self, field: str, alias: str, canonical: str) -> None:
        key = (field, normalize_match(alias))
        previous = self._aliases.get(key)
        if previous is not None and previous != canonical:
            raise TaggingError(f"ambiguous alias: {field}:{alias}")
        self._aliases[key] = canonical

    def resolve(self, field: str, value: str) -> str:
        return self._aliases.get((field, normalize_match(value)), value.strip())


def migrate_snapshots(
    snapshots: list[dict[str, Any]],
    alias_document: dict[str, Any],
    *,
    correction_document: dict[str, Any] | None = None,
    taxonomy_version: str,
    alias_version: str,
    algorithm_version: str,
    scope_decision_version: str,
    generated_at: str | None = None,
) -> dict[str, Any]:
    resolver = AliasResolver(_merge_alias_corrections(alias_document, correction_document))
    registry: dict[str, CanonicalTag] = {}
    videos: dict[str, dict[str, Any]] = {}
    assignment_count = 0

    for snapshot in snapshots:
        raw_videos = snapshot.get("videos", [])
        if not isinstance(raw_videos, list):
            raise TaggingError("videos must be an array")
        for raw_video in cast(list[object], raw_videos):
            video = _object(raw_video)
            video_id = _string(video, "videoId")
            if video_id in videos:
                raise TaggingError(f"duplicate videoId across populations: {video_id}")
            corrected_video = _apply_assignment_corrections(video, correction_document)
            migrated = _migrate_video(corrected_video, resolver, registry)
            assignment_count += len(migrated["tagAssignments"])
            videos[video_id] = migrated

    generated = generated_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    ordered_videos = [videos[key] for key in sorted(videos)]
    _validate_population(ordered_videos)
    return {
        "schemaVersion": "3.0.0",
        "taxonomyVersion": taxonomy_version,
        "aliasVersion": alias_version,
        "algorithmVersion": algorithm_version,
        "scopeDecisionVersion": scope_decision_version,
        "correctionVersion": (
            correction_document.get("correctionVersion")
            if correction_document is not None
            else None
        ),
        "generatedAt": generated,
        "sources": ["video_tags_v2.json", "collaboration_video_tags_v2.json"],
        "videoCount": len(ordered_videos),
        "assignmentCount": assignment_count,
        "tagDefinitions": [
            {
                "tagId": tag.tag_id,
                "categoryId": tag.category_id,
                "subcategoryId": tag.subcategory_id,
                "canonicalName": tag.canonical_name,
                "displayName": tag.display_name,
                "status": "active",
                "introducedInVersion": "3.0.0",
            }
            for tag in sorted(registry.values(), key=lambda item: item.tag_id)
        ],
        "videos": ordered_videos,
    }


def _apply_assignment_corrections(
    video: dict[str, Any], correction_document: dict[str, Any] | None
) -> dict[str, Any]:
    if correction_document is None:
        return video
    raw_corrections = correction_document.get("assignmentCorrections", [])
    if not isinstance(raw_corrections, list):
        raise TaggingError("assignmentCorrections must be an array")

    tags = video.get("tags", [])
    if not isinstance(tags, list):
        raise TaggingError("tags must be an array")
    corrected_tags = [dict(_object(tag)) for tag in cast(list[object], tags)]
    existing = {
        (
            assignment.get("categoryId"),
            assignment.get("subcategoryId"),
            assignment.get("tag"),
        )
        for assignment in corrected_tags
    }
    changed = False
    for raw in cast(list[object], raw_corrections):
        correction = _object(raw)
        if correction.get("operation") != "add":
            raise TaggingError("unsupported assignment correction operation")
        if correction.get("videoId") != video.get("videoId"):
            continue
        if correction.get("evidenceType") != "metadata_title":
            raise TaggingError("assignment correction requires metadata_title evidence")
        assignment = _object(correction.get("assignment"))
        identity = (
            assignment.get("categoryId"),
            assignment.get("subcategoryId"),
            assignment.get("tag"),
        )
        if identity not in existing:
            corrected_tags.append(dict(assignment))
            existing.add(identity)
            changed = True

    return {**video, "tags": corrected_tags} if changed else video


def _merge_alias_corrections(
    alias_document: dict[str, Any], correction_document: dict[str, Any] | None
) -> dict[str, Any]:
    if correction_document is None:
        return alias_document
    records = correction_document.get("records", [])
    if not isinstance(records, list):
        raise TaggingError("correction records must be an array")
    aliases = alias_document.get("exactAliases", [])
    if not isinstance(aliases, list):
        raise TaggingError("exactAliases must be an array")
    corrected = [*cast(list[object], aliases)]
    for raw in cast(list[object], records):
        record = _object(raw)
        if record.get("evidenceType") != "channel_id_identity":
            raise TaggingError("correction requires channel_id_identity evidence")
        channel_id = record.get("channelId")
        if not isinstance(channel_id, str) or not channel_id:
            raise TaggingError("correction requires channelId")
        corrected.append(
            {
                "field": _string(record, "field"),
                "canonical": _string(record, "canonical"),
                "aliases": record.get("aliases", []),
            }
        )
    return {**alias_document, "exactAliases": corrected}


def public_tag_index(snapshot: dict[str, Any], release_id: str) -> dict[str, Any]:
    videos = snapshot.get("videos", [])
    definitions = snapshot.get("tagDefinitions", [])
    if not isinstance(videos, list) or not isinstance(definitions, list):
        raise TaggingError("invalid canonical snapshot")
    by_tag: dict[str, set[str]] = {}
    for raw_video in cast(list[object], videos):
        video = _object(raw_video)
        video_id = _string(video, "videoId")
        assignments = video.get("tagAssignments", [])
        if not isinstance(assignments, list):
            raise TaggingError("tagAssignments must be an array")
        for raw in cast(list[object], assignments):
            tag_id = _string(_object(raw), "tagId")
            by_tag.setdefault(tag_id, set()).add(video_id)
    tags: list[dict[str, Any]] = []
    for raw in cast(list[object], definitions):
        definition = _object(raw)
        tag_id = _string(definition, "tagId")
        video_ids = sorted(by_tag.get(tag_id, set()))
        tags.append({**definition, "count": len(video_ids), "videoIds": video_ids})
    return {
        "schemaVersion": "3.0.0",
        "releaseId": release_id,
        "generatedAt": snapshot["generatedAt"],
        "tags": tags,
    }


def _migrate_video(
    video: dict[str, Any], resolver: AliasResolver, registry: dict[str, CanonicalTag]
) -> dict[str, Any]:
    assignments = video.get("tags", [])
    if not isinstance(assignments, list):
        raise TaggingError("tags must be an array")
    migrated: list[dict[str, Any]] = []
    seen: set[str] = set()
    for raw in cast(list[object], assignments):
        assignment = _object(raw)
        category_id = _string(assignment, "categoryId")
        subcategory_id = _string(assignment, "subcategoryId")
        field = f"{category_id}.{subcategory_id}"
        canonical = resolver.resolve(field, _string(assignment, "tag"))
        if canonical in BLOCKED_VALUES:
            raise TaggingError(f"blocked assignment value: {canonical}")
        confidence = _string(assignment, "confidence")
        if confidence not in {"high", "medium"}:
            raise TaggingError(f"invalid confidence: {confidence}")
        tag_id = stable_tag_id(category_id, subcategory_id, canonical)
        if tag_id in seen:
            raise TaggingError(f"duplicate tag assignment: {video.get('videoId')}:{tag_id}")
        seen.add(tag_id)
        registry.setdefault(
            tag_id,
            CanonicalTag(tag_id, category_id, subcategory_id, canonical, canonical),
        )
        migrated.append(
            {
                "videoId": _string(video, "videoId"),
                "tagId": tag_id,
                "categoryId": category_id,
                "category": _string(assignment, "category"),
                "subcategoryId": subcategory_id,
                "subcategory": _string(assignment, "subcategory"),
                "tag": canonical,
                "reason": _string(assignment, "reason"),
                "source": _normalized_source(_string(assignment, "source")),
                "evidence": _string(assignment, "evidence"),
                "confidence": confidence,
            }
        )
    result = {
        key: video.get(key)
        for key in ("videoId", "title", "publishedAt", "channelTitle", "duration")
    }
    result["tagAssignments"] = sorted(migrated, key=lambda item: cast(str, item["tagId"]))
    return result


def _validate_population(videos: list[dict[str, Any]]) -> None:
    for video in videos:
        counts: dict[str, int] = {}
        assignments = cast(list[dict[str, Any]], video["tagAssignments"])
        for assignment in assignments:
            field = f"{assignment['categoryId']}.{assignment['subcategoryId']}"
            counts[field] = counts.get(field, 0) + 1
        for field in SINGLETON_FIELDS:
            if counts.get(field) != 1:
                raise TaggingError(f"{video['videoId']} requires exactly one {field}")


def _normalized_source(value: str) -> str:
    result = value
    for old, new in SOURCE_REWRITES.items():
        result = re.sub(rf"\b{re.escape(old)}\b", new, result)
    return result


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TaggingError("expected object")
    return cast(dict[str, Any], value)


def _string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise TaggingError(f"{key} must be a non-empty string")
    return item
