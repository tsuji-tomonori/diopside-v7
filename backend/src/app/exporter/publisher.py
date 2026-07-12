from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, cast

from defusedxml import ElementTree as ET
from defusedxml.common import DefusedXmlException

from app.contracts.public import LatestRelease, ReleaseIndex
from app.processing.pipeline import PRIVATE_FIELDS


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
        search_records = self._video_records(documents["search"])
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
