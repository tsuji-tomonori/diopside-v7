from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast
from zipfile import ZipFile

from app.tagging.pipeline import migrate_snapshots, public_tag_index


def _read(zip_file: ZipFile, name: str) -> dict[str, Any]:
    value = cast(object, json.loads(zip_file.read(name)))
    if not isinstance(value, dict):
        raise ValueError(f"{name} root must be an object")
    return cast(dict[str, Any], value)


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate received v2 tags to canonical v3 tagIds")
    parser.add_argument("--tags-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--public-index", type=Path)
    parser.add_argument("--release-id", default="migration-preview")
    args = parser.parse_args()
    with ZipFile(args.tags_zip) as archive:
        own = _read(archive, "tags/video_tags_v2.json")
        external = _read(archive, "tags/collaboration_video_tags_v2.json")
        aliases = _read(archive, "tags/tag_aliases_v2.json")
    snapshot = migrate_snapshots(
        [own, external],
        aliases,
        taxonomy_version="2.0.0",
        alias_version="2.0.0",
        algorithm_version="tag-migration-v1",
        scope_decision_version="20260711-v1",
    )
    _write(args.output, snapshot)
    if args.public_index:
        _write(args.public_index, public_tag_index(snapshot, args.release_id))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
