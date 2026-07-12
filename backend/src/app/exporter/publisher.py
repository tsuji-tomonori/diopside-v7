from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

from app.contracts.public import LatestRelease, ReleaseIndex


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
        for name, document in documents.items():
            if document.get("releaseId") != release.releaseId:
                raise ReleaseRejected("release_join_mismatch", name)
        search_videos = self._video_ids(documents["search"])
        index_videos = {video.videoId for video in release.videos}
        if search_videos != index_videos:
            raise ReleaseRejected("video_population_mismatch", "index/search")
        tag_ids = self._tag_ids(documents["tags"])
        for video in release.videos:
            if not set(video.tagIds).issubset(tag_ids):
                raise ReleaseRejected("unknown_tag_id", video.videoId)
            detail_path = release_dir / "videos" / f"{video.videoId}.json"
            detail = self.load_document(detail_path)
            if detail.get("videoId") != video.videoId:
                raise ReleaseRejected("detail_join_mismatch", video.videoId)
            if detail.get("releaseId", release.releaseId) != release.releaseId:
                raise ReleaseRejected("release_join_mismatch", video.videoId)
        hashes = {name: sha256(document) for name, document in documents.items()}
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
        latest = {
            "schemaVersion": index["schemaVersion"],
            "releaseId": result.release_id,
            "generatedAt": index["generatedAt"],
            "releaseMode": index["releaseMode"],
            "normalizationVersion": index["normalizationVersion"],
            "indexPath": f"data/releases/{result.release_id}/index.json",
            "searchIndexPath": f"data/releases/{result.release_id}/search-index.json",
            "tagTaxonomyPath": f"data/releases/{result.release_id}/tag-taxonomy.json",
            "tagIndexPath": f"data/releases/{result.release_id}/tag-index.json",
            "tagAliasIndexPath": f"data/releases/{result.release_id}/tag-alias-index.json",
            "artifactHashes": result.artifact_hashes,
        }
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
        base = ReleaseIndex.model_validate(
            self.validator.load_document(
                self.public_dir / "releases" / latest.releaseId / "index.json"
            )
        )
        candidate = ReleaseIndex.model_validate(index)
        base_ids = {video.videoId for video in base.videos}
        candidate_ids = {video.videoId for video in candidate.videos}
        if not candidate_ids.issubset(base_ids):
            raise ReleaseRejected("purge_adds_video", str(candidate_ids - base_ids))
        if any(video.tagIds for video in candidate.videos):
            raise ReleaseRejected("purge_contains_tags", candidate.releaseId)
