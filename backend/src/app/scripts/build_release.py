from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from app.exporter.publisher import NormalReleaseBuilder


def _object(path: Path) -> dict[str, Any]:
    value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON object required: {path}")
    return cast(dict[str, Any], value)


def main() -> int:
    parser = argparse.ArgumentParser(description="正規の通常release候補を構築する")
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--tags", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path, required=True)
    parser.add_argument("--aliases", type=Path, required=True)
    parser.add_argument("--official-channel-id", required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata_document = _object(args.metadata)
    raw_items = metadata_document.get("items", metadata_document.get("videos", []))
    if not isinstance(raw_items, list):
        parser.error("metadata must contain items or videos array")
    result = NormalReleaseBuilder().build(
        args.output,
        release_id=args.release_id,
        metadata=[
            cast(dict[str, Any], item)
            for item in cast(list[object], raw_items)
            if isinstance(item, dict)
        ],
        tag_snapshot=_object(args.tags),
        taxonomy=_object(args.taxonomy),
        aliases=_object(args.aliases),
        official_channel_id=args.official_channel_id,
        generated_at=args.generated_at,
    )
    print(json.dumps({"releaseId": result.release_id, "videoCount": result.video_count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
