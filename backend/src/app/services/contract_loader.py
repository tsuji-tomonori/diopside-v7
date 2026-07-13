from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from fastapi import HTTPException

from app.contracts.public import LatestRelease, ReleaseIndex


def _json_load(path: Path) -> dict[str, Any]:
    try:
        return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"contract not found: {path}") from error
    except json.JSONDecodeError as error:
        raise HTTPException(status_code=500, detail=f"invalid contract json: {path}") from error


def read_public_contract(base_dir: Path, relative_path: str) -> dict[str, Any]:
    target = (base_dir / relative_path).resolve()
    if not target.is_relative_to(base_dir.resolve()):
        raise HTTPException(status_code=400, detail="invalid path")
    return _json_load(target)


def read_latest(base_dir: Path) -> dict[str, Any]:
    latest = LatestRelease.model_validate(_json_load(base_dir / "latest.json"))
    return latest.model_dump(mode="json")


def read_release(base_dir: Path, release_id: str) -> dict[str, Any]:
    release = ReleaseIndex.model_validate(
        _json_load(base_dir / "releases" / release_id / "index.json")
    )
    if release.releaseId != release_id:
        raise HTTPException(status_code=500, detail="releaseId does not match request path")
    return release.model_dump(mode="json")


def read_search_index(base_dir: Path, release_id: str) -> dict[str, Any]:
    return _json_load(base_dir / "releases" / release_id / "search-index.json")


def read_tag_index(base_dir: Path, release_id: str) -> dict[str, Any]:
    return _json_load(base_dir / "releases" / release_id / "tag-index.json")


def read_alias_index(base_dir: Path, release_id: str) -> dict[str, Any]:
    return _json_load(base_dir / "releases" / release_id / "tag-alias-index.json")


def read_taxonomy(base_dir: Path, release_id: str) -> dict[str, Any]:
    return _json_load(base_dir / "releases" / release_id / "tag-taxonomy.json")


def read_video(base_dir: Path, release_id: str, video_id: str) -> dict[str, Any]:
    return _json_load(base_dir / "releases" / release_id / "videos" / f"{video_id}.json")
