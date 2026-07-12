from __future__ import annotations

import sys
from pathlib import Path

from app.contracts.public import LatestRelease, ReleaseIndex


def _ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    base = Path(__file__).resolve().parents[3] / "data" / "public"
    latest_path = base / "latest.json"
    _ensure(latest_path.exists(), "latest.json is required")

    latest = LatestRelease.model_validate_json(latest_path.read_text(encoding="utf-8"))
    release_id = latest.releaseId
    release_dir = base / "releases" / release_id

    release = ReleaseIndex.model_validate_json(
        (release_dir / "index.json").read_text(encoding="utf-8")
    )
    _ensure(release.releaseId == release_id, "releaseId mismatch")
    _ensure(release.releaseMode == latest.releaseMode, "releaseMode mismatch")
    _ensure(
        release.normalizationVersion == latest.normalizationVersion,
        "normalizationVersion mismatch",
    )

    expected_paths = [
        latest.indexPath,
        latest.searchIndexPath,
    ]
    if latest.releaseMode == "normal":
        expected_paths.extend(
            path
            for path in (
                latest.tagTaxonomyPath,
                latest.tagIndexPath,
                latest.tagAliasIndexPath,
            )
            if path is not None
        )
    for public_path in expected_paths:
        relative = public_path.removeprefix("data/")
        _ensure((base / relative).is_file(), f"referenced artifact is missing: {public_path}")

    for video in release.videos:
        detail_path = release_dir / "videos" / f"{video.videoId}.json"
        _ensure(detail_path.is_file(), f"video detail is missing: {video.videoId}")

    print(f"ok: release {release_id} with {len(release.videos)} videos")
    return 0


if __name__ == "__main__":
    sys.exit(main())
