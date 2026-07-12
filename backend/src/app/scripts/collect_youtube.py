from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast

from app.collectors.youtube import JsonCheckpoint, YouTubeDataClient
from app.core.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect a YouTube channel uploads snapshot")
    parser.add_argument("--channel-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    args = parser.parse_args()

    settings = get_settings()
    if not settings.youtube_api_key:
        parser.error("DIO_YOUTUBE_API_KEY is required")

    with YouTubeDataClient(
        settings.youtube_api_key, base_url=settings.youtube_api_base_url
    ) as client:
        channel = client.channel(args.channel_id)
        if channel is None:
            raise SystemExit("channel not found")
        details_value = cast(object, channel.get("contentDetails"))
        details = cast(dict[str, Any], details_value) if isinstance(details_value, dict) else {}
        related_value = details.get("relatedPlaylists")
        related = cast(dict[str, Any], related_value) if isinstance(related_value, dict) else {}
        playlist_id = related.get("uploads")
        if not isinstance(playlist_id, str):
            raise SystemExit("uploads playlist not found")
        upload_items = list(client.uploads(playlist_id, JsonCheckpoint(args.checkpoint)))
        video_ids = [
            item.get("contentDetails", {}).get("videoId")
            for item in upload_items
            if isinstance(item.get("contentDetails"), dict)
        ]
        videos = list(client.videos([value for value in video_ids if isinstance(value, str)]))
        payload = {
            "schemaVersion": "1.0.0",
            "source": "YouTube Data API v3",
            "channel": channel,
            "videos": videos,
            "quota": client.quota_report(),
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(f"{args.output.suffix}.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
