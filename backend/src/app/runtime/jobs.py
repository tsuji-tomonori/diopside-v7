# pyright: reportUnknownMemberType=false

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, cast

import boto3

from app.collectors.youtube import JsonCheckpoint, YouTubeDataClient


class ObjectStore(Protocol):
    def put_object(self, **kwargs: object) -> object: ...


class SecretStore(Protocol):
    def get_secret_value(self, **kwargs: object) -> dict[str, Any]: ...


def metadata_sync(job: dict[str, Any]) -> dict[str, Any]:
    target_id = _target(job)
    with _youtube() as client:
        channel = client.channel(target_id)
        if channel is None:
            raise ValueError("channel not found")
        details = _object(channel.get("contentDetails"))
        playlist_id = _object(details.get("relatedPlaylists")).get("uploads")
        if not isinstance(playlist_id, str):
            raise ValueError("uploads playlist not found")
        uploads = list(client.uploads(playlist_id))
        ids = [
            value
            for item in uploads
            for value in [_object(item.get("contentDetails")).get("videoId")]
            if isinstance(value, str)
        ]
        payload = {
            "schemaVersion": "1.0.0",
            "source": "YouTube Data API v3",
            "fetchedAt": _now(),
            "channel": channel,
            "videos": list(client.videos(ids)),
            "quota": client.quota_report(),
        }
    return _write_raw(job, "metadata", payload)


def comment_collect(job: dict[str, Any]) -> dict[str, Any]:
    video_id = _target(job)
    with _youtube() as client:
        payload = {
            "schemaVersion": "1.0.0",
            "videoId": video_id,
            "fetchedAt": _now(),
            "threads": list(client.comments(video_id)),
            "quota": client.quota_report(),
        }
    return _write_raw(job, "comments", payload)


def live_chat_collect(job: dict[str, Any]) -> dict[str, Any]:
    manifest = _object(job.get("inputManifest"))
    live_chat_id = manifest.get("liveChatId")
    if not isinstance(live_chat_id, str) or not live_chat_id:
        raise ValueError("inputManifest.liveChatId is required")
    checkpoint_name = hashlib.sha256(str(job["jobId"]).encode()).hexdigest()
    checkpoint = JsonCheckpoint(Path(tempfile.gettempdir()) / f"{checkpoint_name}.json")
    with _youtube() as client:
        result = client.collect_live_chat(live_chat_id, checkpoint)
        payload = {
            "schemaVersion": "1.0.0",
            "videoId": _target(job),
            "collectedAt": _now(),
            "status": result.status,
            "nextPageToken": result.next_page_token,
            "pollingIntervalMillis": result.polling_interval_ms,
            "messages": result.messages,
            "quota": client.quota_report(),
        }
    return _write_raw(job, "live-chat", payload)


def _youtube() -> YouTubeDataClient:
    key = os.environ.get("DIO_YOUTUBE_API_KEY")
    secret_arn = os.environ.get("YOUTUBE_API_KEY_SECRET_ARN")
    if not key and secret_arn:
        secrets = cast(SecretStore, boto3.client("secretsmanager"))
        response = secrets.get_secret_value(SecretId=secret_arn)
        value = response.get("SecretString")
        key = value if isinstance(value, str) else None
    if not key:
        raise RuntimeError("YouTube API key secret is required")
    return YouTubeDataClient(
        key,
        base_url=os.environ.get(
            "DIO_YOUTUBE_API_BASE_URL", "https://www.googleapis.com/youtube/v3"
        ),
    )


def _write_raw(job: dict[str, Any], kind: str, payload: object) -> dict[str, Any]:
    bucket = _required_env("RAW_BUCKET")
    key = f"raw/{kind}/{_target(job)}/{job['inputVersion']}/{job['jobId']}.json"
    store = cast(ObjectStore, boto3.client("s3"))
    body = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    store.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
    return {"bucket": bucket, "key": key, "bytes": len(body)}


def _target(job: dict[str, Any]) -> str:
    value = job.get("targetId")
    if not isinstance(value, str) or not value:
        raise ValueError("targetId is required")
    return value


def _object(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
