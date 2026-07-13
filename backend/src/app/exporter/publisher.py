from __future__ import annotations

import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from app.contracts.public import LatestRelease, ReleaseIndex
from app.processing.pipeline import PRIVATE_FIELDS, tokenize


class ReleaseRejected(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ValidationResult:
    release_id: str
    artifact_hashes: dict[str, str]
    video_count: int


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def sha256(value: object) -> str:
    return f"sha256:{hashlib.sha256(canonical_json(value)).hexdigest()}"


class ReleaseValidator:
    REQUIRED_ROOTS: ClassVar[dict[str, str]] = {
        "index": "index.json",
        "search": "search-index.json",
    }
    NORMAL_ROOTS: ClassVar[dict[str, str]] = {
        "taxonomy": "tag-taxonomy.json",
        "tags": "tag-index.json",
        "aliases": "tag-alias-index.json",
    }

    def validate(self, release_dir: Path) -> ValidationResult:
        documents = {
            name: self.load_document(release_dir / relative)
            for name, relative in self.REQUIRED_ROOTS.items()
        }
        release = ReleaseIndex.model_validate(documents["index"])
        if release.releaseMode == "normal":
            documents.update(
                {
                    name: self.load_document(release_dir / relative)
                    for name, relative in self.NORMAL_ROOTS.items()
                }
            )
        for name, document in documents.items():
            if document.get("releaseId") != release.releaseId:
                raise ReleaseRejected("release_join_mismatch", name)
        search_videos = self._video_ids(documents["search"])
        search_records = self._video_records(documents["search"])
        index_videos = {video.videoId for video in release.videos}
        if search_videos != index_videos:
            raise ReleaseRejected("video_population_mismatch", "index/search")
        tag_ids: set[str] = self._tag_ids(documents["tags"]) if "tags" in documents else set()
        for video in release.videos:
            if not set(video.tagIds or []).issubset(tag_ids):
                raise ReleaseRejected("unknown_tag_id", video.videoId)
            detail_path = release_dir / "videos" / f"{video.videoId}.json"
            detail = self.load_document(detail_path)
            if detail.get("videoId") != video.videoId:
                raise ReleaseRejected("detail_join_mismatch", video.videoId)
            if detail.get("releaseId", release.releaseId) != release.releaseId:
                raise ReleaseRejected("release_join_mismatch", video.videoId)
            flags = video.artifactFlags.model_dump()
            if detail.get("artifactFlags") != flags:
                raise ReleaseRejected("artifact_contract_mismatch", video.videoId)
            if search_records[video.videoId].get("artifactFlags") != flags:
                raise ReleaseRejected("artifact_contract_mismatch", video.videoId)
            self._validate_artifacts(release_dir, video.videoId, flags, detail)
        hashes: dict[str, str] = {}
        for path in sorted(value for value in release_dir.rglob("*") if value.is_file()):
            relative = path.relative_to(release_dir).as_posix()
            if path.suffix == ".json":
                document = self.load_document(path)
                self._reject_private(document, relative)
                hashes[relative] = sha256(document)
            elif path.suffix == ".svg":
                self._validate_svg(path)
                hashes[relative] = f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
            else:
                raise ReleaseRejected("unsupported_artifact", relative)
        return ValidationResult(release.releaseId, hashes, len(index_videos))

    def load_document(self, path: Path) -> dict[str, Any]:
        try:
            value = cast(object, json.loads(path.read_text(encoding="utf-8")))
        except FileNotFoundError as error:
            raise ReleaseRejected("missing_artifact", str(path)) from error
        except json.JSONDecodeError as error:
            raise ReleaseRejected("invalid_json", str(path)) from error
        if not isinstance(value, dict):
            raise ReleaseRejected("invalid_schema", str(path))
        return cast(dict[str, Any], value)

    def _video_ids(self, document: dict[str, Any]) -> set[str]:
        values = document.get("videos", [])
        if not isinstance(values, list):
            raise ReleaseRejected("invalid_schema", "search videos")
        result: set[str] = set()
        for raw in cast(list[object], values):
            if not isinstance(raw, dict):
                raise ReleaseRejected("invalid_schema", "search video")
            item = cast(dict[str, Any], raw)
            video_id = item.get("videoId")
            if not isinstance(video_id, str) or video_id in result:
                raise ReleaseRejected("invalid_video_id", str(video_id))
            result.add(video_id)
        return result

    def _video_records(self, document: dict[str, Any]) -> dict[str, dict[str, Any]]:
        values = document.get("videos", [])
        if not isinstance(values, list):
            raise ReleaseRejected("invalid_schema", "search videos")
        return {
            video_id: item
            for raw in cast(list[object], values)
            if isinstance(raw, dict)
            for item in [cast(dict[str, Any], raw)]
            for video_id in [item.get("videoId")]
            if isinstance(video_id, str)
        }

    def _tag_ids(self, document: dict[str, Any]) -> set[str]:
        values = document.get("tags", [])
        if not isinstance(values, list):
            raise ReleaseRejected("invalid_schema", "tag index")
        return {
            value
            for raw in cast(list[object], values)
            if isinstance(raw, dict)
            for value in [cast(dict[str, Any], raw).get("tagId")]
            if isinstance(value, str)
        }

    def _validate_artifacts(
        self,
        release_dir: Path,
        video_id: str,
        flags: dict[str, bool],
        detail: dict[str, Any],
    ) -> None:
        for field in ("chat", "comments", "timestamps"):
            if flags[field] != (field in detail):
                raise ReleaseRejected("artifact_contract_mismatch", f"{video_id}:{field}")
        for source, flag in (
            ("chat", "wordcloudChat"),
            ("comments", "wordcloudComments"),
            ("both", "wordcloudBoth"),
        ):
            svg = release_dir / "wordcloud" / f"{video_id}-{source}.svg"
            metadata = release_dir / "wordcloud" / f"{video_id}-{source}.json"
            exists = svg.is_file() and metadata.is_file()
            if flags[flag] != exists:
                raise ReleaseRejected("artifact_contract_mismatch", f"{video_id}:{flag}")

    def _reject_private(self, value: object, location: str) -> None:
        if isinstance(value, dict):
            for key, child in cast(dict[object, object], value).items():
                if isinstance(key, str) and key in PRIVATE_FIELDS:
                    raise ReleaseRejected("private_field", f"{location}:{key}")
                self._reject_private(child, location)
        elif isinstance(value, list):
            for child in cast(list[object], value):
                self._reject_private(child, location)

    def _validate_svg(self, path: Path) -> None:
        try:
            root = ET.fromstring(path.read_bytes())
        except (ET.ParseError, DefusedXmlException) as error:
            raise ReleaseRejected("unsafe_svg", path.name) from error
        for element in root.iter():
            name = element.tag.rsplit("}", 1)[-1].casefold()
            if name in {"script", "foreignobject", "iframe", "object", "embed"}:
                raise ReleaseRejected("unsafe_svg", path.name)
            for attribute, value in element.attrib.items():
                attribute_name = attribute.rsplit("}", 1)[-1].casefold()
                if attribute_name.startswith("on") or (
                    attribute_name == "href" and not value.startswith("#")
                ):
                    raise ReleaseRejected("unsafe_svg", path.name)


class AtomicPublisher:
    def __init__(self, public_dir: Path, validator: ReleaseValidator | None = None) -> None:
        self.public_dir = public_dir
        self.validator = validator or ReleaseValidator()

    def publish(self, candidate_dir: Path) -> ValidationResult:
        result = self.validator.validate(candidate_dir)
        destination = self.public_dir / "releases" / result.release_id
        if destination.exists():
            raise ReleaseRejected("release_exists", result.release_id)
        self._validate_mode_transition(candidate_dir)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.publishing")
        if temporary.exists():
            shutil.rmtree(temporary)
        shutil.copytree(candidate_dir, temporary)
        temporary.replace(destination)
        index = self.validator.load_document(destination / "index.json")
        latest: dict[str, Any] = {
            "schemaVersion": index["schemaVersion"],
            "releaseId": result.release_id,
            "generatedAt": index["generatedAt"],
            "releaseMode": index["releaseMode"],
            "normalizationVersion": index["normalizationVersion"],
            "indexPath": f"data/releases/{result.release_id}/index.json",
            "searchIndexPath": f"data/releases/{result.release_id}/search-index.json",
            "artifactHashes": result.artifact_hashes,
        }
        if index["releaseMode"] == "normal":
            latest.update(
                {
                    "tagTaxonomyPath": f"data/releases/{result.release_id}/tag-taxonomy.json",
                    "tagIndexPath": f"data/releases/{result.release_id}/tag-index.json",
                    "tagAliasIndexPath": f"data/releases/{result.release_id}/tag-alias-index.json",
                }
            )
        else:
            latest.update(
                {
                    key: index[key]
                    for key in (
                        "purgeBaseReleaseId",
                        "purgeBaseManifestSha256",
                        "purgeTrigger",
                    )
                    if key in index
                }
            )
        LatestRelease.model_validate(latest)
        latest_path = self.public_dir / "latest.json"
        latest_temporary = self.public_dir / ".latest.json.tmp"
        latest_temporary.write_bytes(canonical_json(latest) + b"\n")
        latest_temporary.replace(latest_path)
        return result

    def _validate_mode_transition(self, candidate_dir: Path) -> None:
        index = self.validator.load_document(candidate_dir / "index.json")
        if index.get("releaseMode") != "compliance_purge":
            return
        latest_path = self.public_dir / "latest.json"
        if not latest_path.exists():
            raise ReleaseRejected("purge_without_base", "latest.json")
        latest = LatestRelease.model_validate(self.validator.load_document(latest_path))
        latest_document = self.validator.load_document(latest_path)
        base = ReleaseIndex.model_validate(
            self.validator.load_document(
                self.public_dir / "releases" / latest.releaseId / "index.json"
            )
        )
        candidate = ReleaseIndex.model_validate(index)
        if candidate.purgeBaseReleaseId != latest.releaseId:
            raise ReleaseRejected("stale_purge_base", candidate.releaseId)
        if candidate.purgeBaseManifestSha256 != sha256(latest_document):
            raise ReleaseRejected("stale_purge_base", candidate.releaseId)
        base_ids = {video.videoId for video in base.videos}
        candidate_ids = {video.videoId for video in candidate.videos}
        if not candidate_ids.issubset(base_ids):
            raise ReleaseRejected("purge_adds_video", str(candidate_ids - base_ids))
        if any(video.tagIds for video in candidate.videos):
            raise ReleaseRejected("purge_contains_tags", candidate.releaseId)


class CompliancePurgeBuilder:
    DERIVED_FIELDS: ClassVar[tuple[str, ...]] = (
        "chat",
        "comments",
        "timestamps",
        "wordcloud",
    )

    def build(
        self,
        base_dir: Path,
        output_dir: Path,
        *,
        release_id: str,
        latest_document: dict[str, Any],
        excluded_video_ids: set[str],
        trigger: str,
        generated_at: str,
    ) -> ValidationResult:
        if output_dir.exists():
            raise ReleaseRejected("release_exists", release_id)
        shutil.copytree(base_dir, output_dir)
        for name in ReleaseValidator.NORMAL_ROOTS.values():
            (output_dir / name).unlink(missing_ok=True)
        shutil.rmtree(output_dir / "wordcloud", ignore_errors=True)

        for name in ("index.json", "search-index.json"):
            path = output_dir / name
            document = ReleaseValidator().load_document(path)
            document.update(
                {
                    "releaseId": release_id,
                    "releaseMode": "compliance_purge",
                    "generatedAt": generated_at,
                    "purgeBaseReleaseId": latest_document["releaseId"],
                    "purgeBaseManifestSha256": sha256(latest_document),
                    "purgeTrigger": trigger,
                }
            )
            document.pop("taxonomyVersion", None)
            document.pop("aliasVersion", None)
            videos = document.get("videos", [])
            if not isinstance(videos, list):
                raise ReleaseRejected("invalid_schema", f"{name}:videos")
            retained: list[dict[str, Any]] = []
            for raw in cast(list[object], videos):
                if not isinstance(raw, dict):
                    raise ReleaseRejected("invalid_schema", f"{name}:video")
                video = cast(dict[str, Any], raw)
                if video.get("videoId") in excluded_video_ids:
                    continue
                video.pop("tagIds", None)
                video["artifactFlags"] = _empty_artifact_flags()
                retained.append(video)
            document["videos"] = retained
            path.write_bytes(canonical_json(document) + b"\n")

        details = output_dir / "videos"
        for path in details.glob("*.json"):
            if path.stem in excluded_video_ids:
                path.unlink()
                continue
            detail = ReleaseValidator().load_document(path)
            detail["releaseId"] = release_id
            detail.pop("tagIds", None)
            detail["artifactFlags"] = _empty_artifact_flags()
            for field in self.DERIVED_FIELDS:
                detail.pop(field, None)
            path.write_bytes(canonical_json(detail) + b"\n")
        return ReleaseValidator().validate(output_dir)


def _empty_artifact_flags() -> dict[str, bool]:
    return {
        "chat": False,
        "comments": False,
        "timestamps": False,
        "wordcloudChat": False,
        "wordcloudComments": False,
        "wordcloudBoth": False,
    }


class NormalReleaseBuilder:
    def build(
        self,
        output_dir: Path,
        *,
        release_id: str,
        metadata: list[dict[str, Any]],
        tag_snapshot: dict[str, Any],
        taxonomy: dict[str, Any],
        aliases: dict[str, Any],
        official_channel_id: str,
        generated_at: str,
    ) -> ValidationResult:
        if output_dir.exists():
            raise ReleaseRejected("release_exists", release_id)
        output_dir.mkdir(parents=True)
        assignments = self._assignments(tag_snapshot)
        definitions = self._definitions(tag_snapshot)
        summaries: list[dict[str, Any]] = []
        search_records: list[dict[str, Any]] = []
        included_ids: set[str] = set()
        for item in sorted(metadata, key=lambda value: str(value.get("videoId", ""))):
            video_id = item.get("videoId")
            if not isinstance(video_id, str) or video_id not in assignments:
                continue
            summary = self._summary(
                item,
                assignments[video_id],
                official_channel_id,
            )
            summaries.append(summary)
            included_ids.add(video_id)
            search_records.append(
                {
                    "videoId": video_id,
                    "titleTokens": tokenize(cast(str, summary["title"])),
                    "sourceKind": summary["sourceKind"],
                    "metadataStatus": summary["metadataStatus"],
                    "publishedAt": summary["publishedAt"],
                    "publishedDate": cast(str, summary["publishedAt"])[:10],
                    "durationSec": summary["durationSec"],
                    "artifactFlags": summary["artifactFlags"],
                    "tagIds": summary["tagIds"],
                }
            )
            detail = {**summary, "releaseId": release_id}
            path = output_dir / "videos" / f"{video_id}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(canonical_json(detail) + b"\n")
        if not summaries:
            raise ReleaseRejected("empty_release", release_id)

        envelope = {
            "schemaVersion": "1.0.0",
            "releaseId": release_id,
            "releaseMode": "normal",
            "generatedAt": generated_at,
        }
        index = {
            **envelope,
            "layout": "monolithic",
            "normalizationVersion": "normalize-v1/tokenizer-v1",
            "taxonomyVersion": str(tag_snapshot.get("taxonomyVersion", "unknown")),
            "aliasVersion": str(tag_snapshot.get("aliasVersion", "unknown")),
            "videos": summaries,
        }
        search = {
            **envelope,
            "layout": "monolithic",
            "normalizationVersion": "normalize-v1/tokenizer-v1",
            "videos": search_records,
        }
        tag_index = {
            **envelope,
            "tags": [
                {
                    **definition,
                    "count": len(video_ids),
                    "videoIds": video_ids,
                }
                for tag_id, definition in sorted(definitions.items())
                for video_ids in [
                    sorted(video_id for video_id in included_ids if tag_id in assignments[video_id])
                ]
                if video_ids
            ],
        }
        documents = {
            "index.json": index,
            "search-index.json": search,
            "tag-index.json": tag_index,
            "tag-taxonomy.json": {**taxonomy, **envelope},
            "tag-alias-index.json": {**aliases, **envelope},
        }
        for name, document in documents.items():
            (output_dir / name).write_bytes(canonical_json(document) + b"\n")
        return ReleaseValidator().validate(output_dir)

    def _assignments(self, snapshot: dict[str, Any]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        videos = snapshot.get("videos", [])
        if not isinstance(videos, list):
            raise ReleaseRejected("invalid_tag_snapshot", "videos")
        for raw in cast(list[object], videos):
            if not isinstance(raw, dict):
                raise ReleaseRejected("invalid_tag_snapshot", "video")
            video = cast(dict[str, Any], raw)
            video_id = video.get("videoId")
            raw_assignments = video.get("tagAssignments", [])
            if not isinstance(video_id, str) or not isinstance(raw_assignments, list):
                raise ReleaseRejected("invalid_tag_snapshot", "assignment")
            result[video_id] = sorted(
                tag_id
                for assignment in cast(list[object], raw_assignments)
                if isinstance(assignment, dict)
                for tag_id in [cast(dict[str, Any], assignment).get("tagId")]
                if isinstance(tag_id, str)
            )
        return result

    def _definitions(self, snapshot: dict[str, Any]) -> dict[str, dict[str, Any]]:
        values = snapshot.get("tagDefinitions", [])
        if not isinstance(values, list):
            raise ReleaseRejected("invalid_tag_snapshot", "tagDefinitions")
        return {
            tag_id: definition
            for raw in cast(list[object], values)
            if isinstance(raw, dict)
            for definition in [cast(dict[str, Any], raw)]
            for tag_id in [definition.get("tagId")]
            if isinstance(tag_id, str)
        }

    def _summary(
        self,
        metadata: dict[str, Any],
        tag_ids: list[str],
        official_channel_id: str,
    ) -> dict[str, Any]:
        required = {
            key: metadata.get(key)
            for key in ("videoId", "title", "publishedAt", "duration", "thumbnail")
        }
        if not all(required.values()):
            raise ReleaseRejected("ineligible_metadata", str(metadata.get("videoId")))
        duration = cast(str, required["duration"])
        duration_sec = _iso_duration_seconds(duration)
        source_updated = metadata.get("fetchedAt") or metadata.get("sourceUpdatedAt")
        if not isinstance(source_updated, str):
            raise ReleaseRejected("ineligible_metadata", cast(str, required["videoId"]))
        return {
            "videoId": required["videoId"],
            "title": required["title"],
            "publishedAt": required["publishedAt"],
            "duration": duration,
            "durationSec": duration_sec,
            "thumbnail": required["thumbnail"],
            "sourceKind": (
                "official_channel"
                if metadata.get("channelId") == official_channel_id
                else "external_collaboration"
            ),
            "metadataStatus": "resolved",
            "sourceUpdatedAt": source_updated,
            "artifactFlags": _empty_artifact_flags(),
            "tagIds": tag_ids,
            "provenance": {
                "titleSource": "youtube_api",
                "publishedSource": "youtube_api",
            },
            "coverage": {
                "coverageStart": required["publishedAt"],
                "coverageEnd": required["publishedAt"],
                "completeFromStart": False,
                "sourceUpdatedAt": source_updated,
            },
        }


def _iso_duration_seconds(value: str) -> int:
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if match is None:
        raise ReleaseRejected("invalid_duration", value)
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds
