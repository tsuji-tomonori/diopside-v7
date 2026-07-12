# pyright: reportUnknownMemberType=false

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Any, Protocol, cast
from zoneinfo import ZoneInfo

import boto3
from botocore.exceptions import ClientError

from app.collectors.youtube import JsonCheckpoint, YouTubeDataClient
from app.exporter.publisher import CompliancePurgeBuilder, ReleaseValidator, canonical_json
from app.operations.policy import QuotaAction, QuotaBudget, quota_action
from app.processing.pipeline import (
    Coverage,
    aggregate_events,
    normalize_chat_message,
    normalize_comment,
    normalize_metadata,
    timestamp_candidates,
    wordcloud_artifact,
)


class ObjectStore(Protocol):
    def put_object(self, **kwargs: object) -> object: ...

    def get_object(self, **kwargs: object) -> dict[str, Any]: ...

    def list_objects_v2(self, **kwargs: object) -> dict[str, Any]: ...

    def delete_objects(self, **kwargs: object) -> object: ...


class SecretStore(Protocol):
    def get_secret_value(self, **kwargs: object) -> dict[str, Any]: ...


class Metrics(Protocol):
    def put_metric_data(self, **kwargs: object) -> object: ...


class Cdn(Protocol):
    def create_invalidation(self, **kwargs: object) -> object: ...


class ControlTable(Protocol):
    def get_item(self, **kwargs: object) -> dict[str, Any]: ...

    def update_item(self, **kwargs: object) -> object: ...


class ReadableBody(Protocol):
    def read(self) -> bytes: ...


def metadata_sync(job: dict[str, Any]) -> dict[str, Any]:
    target_id = _target(job)
    manifest = _object(job.get("inputManifest"))
    max_pages_value = manifest.get("maxUploadPages")
    max_pages = max_pages_value if isinstance(max_pages_value, int) else None
    reserved = reserve_quota(job, 1 + 2 * (max_pages or 50))
    with _youtube() as client:
        channel = client.channel(target_id)
        if channel is None:
            raise ValueError("channel not found")
        details = _object(channel.get("contentDetails"))
        playlist_id = _object(details.get("relatedPlaylists")).get("uploads")
        if not isinstance(playlist_id, str):
            raise ValueError("uploads playlist not found")
        uploads = list(client.uploads(playlist_id, max_pages=max_pages))
        ids = [
            value
            for item in uploads
            for value in [_object(item.get("contentDetails")).get("videoId")]
            if isinstance(value, str)
        ]
        videos = list(client.videos(ids))
        payload = {
            "schemaVersion": "1.0.0",
            "source": "YouTube Data API v3",
            "fetchedAt": _now(),
            "channel": channel,
            "videos": videos,
            "quota": client.quota_report(),
        }
    _record_quota(_object(payload.get("quota")), job, reserved)
    result = _write_raw(job, "metadata", payload)
    _enqueue_child(job, "normalize", target_id, "metadata", {**result, "kind": "metadata"})
    if manifest.get("discoverLive") is True:
        for video in videos:
            live = _object(video.get("liveStreamingDetails"))
            live_chat_id = live.get("activeLiveChatId")
            video_id = video.get("id")
            if isinstance(live_chat_id, str) and isinstance(video_id, str):
                _enqueue_child(
                    job,
                    "live_chat_collect",
                    video_id,
                    f"live-{video_id}",
                    {
                        "liveChatId": live_chat_id,
                        "streamStartedAt": live.get("actualStartTime"),
                        "durationSec": _duration_seconds(
                            _object(video.get("contentDetails")).get("duration")
                        ),
                    },
                )
    if manifest.get("collectComments") is True:
        for video_id in ids:
            _enqueue_child(job, "comment_collect", video_id, f"comments-{video_id}", {})
    return result


def comment_collect(job: dict[str, Any]) -> dict[str, Any]:
    video_id = _target(job)
    reserved = reserve_quota(job, 100)
    with _youtube() as client:
        payload = {
            "schemaVersion": "1.0.0",
            "videoId": video_id,
            "fetchedAt": _now(),
            "threads": list(client.comments(video_id)),
            "quota": client.quota_report(),
        }
    _record_quota(_object(payload.get("quota")), job, reserved)
    result = _write_raw(job, "comments", payload)
    _enqueue_child(job, "normalize", video_id, "normalize", {**result, "kind": "comments"})
    return result


def live_chat_collect(job: dict[str, Any]) -> dict[str, Any]:
    manifest = _object(job.get("inputManifest"))
    live_chat_id = manifest.get("liveChatId")
    if not isinstance(live_chat_id, str) or not live_chat_id:
        raise ValueError("inputManifest.liveChatId is required")
    reserved = reserve_quota(job, 500)
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
    _record_quota(_object(payload.get("quota")), job, reserved)
    result = _write_raw(job, "live-chat", payload)
    _enqueue_child(
        job,
        "normalize",
        _target(job),
        "normalize",
        {**result, "kind": "live-chat", "streamStartedAt": manifest.get("streamStartedAt")},
    )
    return result


def normalize(job: dict[str, Any]) -> dict[str, Any]:
    manifest = _object(job.get("inputManifest"))
    payload = _read_json(manifest)
    kind = manifest.get("kind")
    video_id = _target(job)
    if kind != "metadata":
        _require_gate("GATE-001")
    if kind == "metadata":
        fetched_at = _string(payload.get("fetchedAt"), "payload.fetchedAt")
        items = [normalize_metadata(item, fetched_at) for item in _objects(payload.get("videos"))]
    elif kind == "comments":
        secret = _pseudonym_secret()
        comments = [
            comment
            for thread in _objects(payload.get("threads"))
            for comment in _thread_comments(thread)
        ]
        items = [normalize_comment(item, video_id, secret) for item in comments]
    elif kind in {"live-chat", "replay-chat"}:
        secret = _pseudonym_secret()
        started = _parse_time(_string(manifest.get("streamStartedAt"), "streamStartedAt"))
        items = [
            normalize_chat_message(item, video_id, started, secret)
            for item in _objects(payload.get("messages"))
        ]
    else:
        raise ValueError("inputManifest.kind is invalid")
    result = _write_processed(job, "normalized", {"schemaVersion": "1.0.0", "items": items})
    if kind in {"comments", "live-chat", "replay-chat"}:
        event_times = [
            item["eventAt"]
            for item in items
            if isinstance(item.get("eventAt"), str)
        ]
        if event_times:
            _enqueue_child(
                job,
                "aggregate",
                video_id,
                "aggregate",
                {
                    **result,
                    "source": "comments" if kind == "comments" else "chat",
                    "coverageStart": min(event_times),
                    "coverageEnd": max(event_times),
                    "completeFromStart": manifest.get("completeFromStart") is True,
                    "sourceUpdatedAt": _now(),
                    "durationSec": manifest.get("durationSec"),
                },
            )
    return result


def aggregate(job: dict[str, Any]) -> dict[str, Any]:
    _require_gate("GATE-001")
    manifest = _object(job.get("inputManifest"))
    payload = _read_json(manifest)
    source_value = manifest.get("source")
    if source_value not in {"chat", "comments"}:
        raise ValueError("inputManifest.source is invalid")
    source = source_value
    coverage = _coverage(manifest)
    result = aggregate_events(_objects(payload.get("items")), source, coverage, _now())
    output = _write_processed(job, "aggregates", result)
    duration_value = manifest.get("durationSec")
    if source == "chat" and isinstance(duration_value, int):
        timestamps = timestamp_candidates(
            _target(job), result, duration_value, coverage, _now()
        )
        timestamp_output = _write_processed(job, "timestamps", timestamps)
        output["timestampKey"] = timestamp_output["key"]
    _enqueue_child(job, "wordcloud", _target(job), "wordcloud", {**output, **manifest})
    return output


def wordcloud(job: dict[str, Any]) -> dict[str, Any]:
    _require_gate("GATE-001")
    manifest = _object(job.get("inputManifest"))
    aggregate_payload = _read_json(manifest)
    source_value = manifest.get("source", "both")
    if source_value not in {"chat", "comments", "both"}:
        raise ValueError("inputManifest.source is invalid")
    metadata, svg = wordcloud_artifact(
        _target(job), source_value, aggregate_payload, _coverage(manifest), _now()
    )
    result = _write_processed(job, "wordcloud", metadata)
    if svg is not None:
        svg_result = _write_processed(
            job, "wordcloud", svg, suffix="svg", content_type="image/svg+xml"
        )
        result["svgKey"] = svg_result["key"]
    return result


def static_export(job: dict[str, Any]) -> dict[str, Any]:
    manifest = _object(job.get("inputManifest"))
    store = cast(ObjectStore, boto3.client("s3"))
    public_bucket = _required_env("PUBLIC_BUCKET")
    purge_base_id: str | None = None
    excluded_ids: set[str] = set()
    with TemporaryDirectory(prefix="diopside-release-") as temporary:
        root = Path(temporary)
        trigger = manifest.get("purgeTrigger")
        if isinstance(trigger, str) and trigger:
            latest = _read_json_object(
                _read_body(store.get_object(Bucket=public_bucket, Key="data/latest.json")),
                "latest.json",
            )
            purge_base_id = _string(latest.get("releaseId"), "latest.releaseId")
            base = root / "base"
            _download_prefix(
                store, public_bucket, f"data/releases/{purge_base_id}", base
            )
            raw_excluded = manifest.get("excludeVideoIds", [])
            excluded_ids = {
                value
                for value in cast(list[object], raw_excluded)
                if isinstance(raw_excluded, list) and isinstance(value, str)
            }
            candidate = root / "candidate"
            release_id = str(manifest.get("releaseId") or f"purge-{job['jobId'][:32]}")
            CompliancePurgeBuilder().build(
                base,
                candidate,
                release_id=release_id,
                latest_document=latest,
                excluded_video_ids=excluded_ids,
                trigger=trigger,
                generated_at=_now(),
            )
            keys = [
                PurePosixPath(path.relative_to(candidate).as_posix())
                for path in sorted(candidate.rglob("*"))
                if path.is_file()
            ]
        else:
            source_bucket = _string(
                manifest.get("bucket", os.environ.get("PROCESSED_BUCKET")),
                "inputManifest.bucket",
            )
            prefix = _string(
                manifest.get("candidatePrefix"), "inputManifest.candidatePrefix"
            ).strip("/")
            candidate = root / "candidate"
            keys = _download_prefix(store, source_bucket, prefix, candidate)
        validation = ReleaseValidator().validate(candidate)
        index = _read_path_json(candidate / "index.json")
        if index.get("releaseMode") == "normal":
            _require_valid_gates(store, manifest)
        release_root = f"data/releases/{validation.release_id}"
        for relative in keys:
            body = (candidate / relative).read_bytes()
            destination = f"{release_root}/{relative.as_posix()}"
            content_type = "image/svg+xml" if relative.suffix == ".svg" else "application/json"
            store.put_object(
                Bucket=public_bucket,
                Key=destination,
                Body=body,
                ContentType=content_type,
                CacheControl="public, max-age=300, immutable",
            )
            copied = _read_body(store.get_object(Bucket=public_bucket, Key=destination))
            if hashlib.sha256(copied).digest() != hashlib.sha256(body).digest():
                raise RuntimeError(f"public read-back mismatch: {relative}")
        latest = _latest_manifest(index, validation.artifact_hashes)
        latest_body = canonical_json(latest) + b"\n"
        latest_condition: dict[str, object]
        try:
            current = store.get_object(Bucket=public_bucket, Key="data/latest.json")
            etag = current.get("ETag")
            if not isinstance(etag, str):
                raise RuntimeError("latest pointer has no ETag")
            latest_condition = {"IfMatch": etag}
        except ClientError as error:
            code = error.response.get("Error", {}).get("Code")
            if code not in {"NoSuchKey", "404", "NotFound"}:
                raise
            latest_condition = {"IfNoneMatch": "*"}
        store.put_object(
            Bucket=public_bucket,
            Key="data/latest.json",
            Body=latest_body,
            ContentType="application/json",
            CacheControl="public, max-age=60, must-revalidate",
            **latest_condition,
        )
    if purge_base_id is not None:
        _delete_prefix(store, public_bucket, f"data/releases/{purge_base_id}/")
        for video_id in excluded_ids:
            for bucket_name in ("RAW_BUCKET", "PROCESSED_BUCKET"):
                bucket = os.environ.get(bucket_name)
                if bucket:
                    _delete_matching_video(store, bucket, video_id)
        distribution_id = os.environ.get("DISTRIBUTION_ID")
        if distribution_id:
            cast(Cdn, boto3.client("cloudfront")).create_invalidation(
                DistributionId=distribution_id,
                InvalidationBatch={
                    "CallerReference": str(job["jobId"]),
                    "Paths": {
                        "Quantity": 1,
                        "Items": [f"/data/releases/{purge_base_id}/*"],
                    },
                },
            )
    _emit_metric("SuccessfulExports", 1, {"JobType": "static_export"})
    return {
        "releaseId": validation.release_id,
        "videoCount": validation.video_count,
        "artifactCount": len(keys),
        "latestKey": "data/latest.json",
    }


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


def _write_processed(
    job: dict[str, Any],
    kind: str,
    payload: object,
    *,
    suffix: str = "json",
    content_type: str = "application/json",
) -> dict[str, Any]:
    bucket = _required_env("PROCESSED_BUCKET")
    key = f"processed/{kind}/{_target(job)}/{job['inputVersion']}/{job['jobId']}.{suffix}"
    body = payload.encode() if isinstance(payload, str) else json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    store = cast(ObjectStore, boto3.client("s3"))
    store.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
    return {"bucket": bucket, "key": key, "bytes": len(body)}


def _read_json(manifest: dict[str, Any]) -> dict[str, Any]:
    bucket = _string(manifest.get("bucket"), "inputManifest.bucket")
    key = _string(manifest.get("key"), "inputManifest.key")
    response = cast(ObjectStore, boto3.client("s3")).get_object(Bucket=bucket, Key=key)
    raw = _read_body(response)
    value = cast(object, json.loads(raw))
    if not isinstance(value, dict):
        raise ValueError("input object must contain a JSON object")
    return cast(dict[str, Any], value)


def _read_body(response: dict[str, Any]) -> bytes:
    return cast(ReadableBody, response.get("Body")).read()


def _download_prefix(
    store: ObjectStore, bucket: str, prefix: str, destination: Path
) -> list[PurePosixPath]:
    token: str | None = None
    paths: list[PurePosixPath] = []
    while True:
        arguments: dict[str, object] = {"Bucket": bucket, "Prefix": f"{prefix}/"}
        if token:
            arguments["ContinuationToken"] = token
        page = store.list_objects_v2(**arguments)
        for item in _objects(page.get("Contents")):
            key = item.get("Key")
            if not isinstance(key, str):
                continue
            relative_value = key.removeprefix(f"{prefix}/")
            relative = PurePosixPath(relative_value)
            if not relative_value or relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe candidate path: {key}")
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_read_body(store.get_object(Bucket=bucket, Key=key)))
            paths.append(relative)
        next_value = page.get("NextContinuationToken")
        token = next_value if isinstance(next_value, str) else None
        if not token:
            break
    if not paths:
        raise ValueError("candidate release is empty")
    return paths


def _read_path_json(path: Path) -> dict[str, Any]:
    value = cast(object, json.loads(path.read_bytes()))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {path.name}")
    return cast(dict[str, Any], value)


def _read_json_object(raw: bytes, name: str) -> dict[str, Any]:
    value = cast(object, json.loads(raw))
    if not isinstance(value, dict):
        raise ValueError(f"JSON object required: {name}")
    return cast(dict[str, Any], value)


def _delete_prefix(store: ObjectStore, bucket: str, prefix: str) -> None:
    token: str | None = None
    while True:
        arguments: dict[str, object] = {"Bucket": bucket, "Prefix": prefix}
        if token:
            arguments["ContinuationToken"] = token
        page = store.list_objects_v2(**arguments)
        objects = [
            {"Key": key}
            for item in _objects(page.get("Contents"))
            for key in [item.get("Key")]
            if isinstance(key, str)
        ]
        if objects:
            store.delete_objects(Bucket=bucket, Delete={"Objects": objects, "Quiet": True})
        next_value = page.get("NextContinuationToken")
        token = next_value if isinstance(next_value, str) else None
        if not token:
            break


def _delete_matching_video(store: ObjectStore, bucket: str, video_id: str) -> None:
    token: str | None = None
    while True:
        arguments: dict[str, object] = {"Bucket": bucket}
        if token:
            arguments["ContinuationToken"] = token
        page = store.list_objects_v2(**arguments)
        objects = [
            {"Key": key}
            for item in _objects(page.get("Contents"))
            for key in [item.get("Key")]
            if isinstance(key, str) and video_id in PurePosixPath(key).parts
        ]
        if objects:
            store.delete_objects(Bucket=bucket, Delete={"Objects": objects, "Quiet": True})
        next_value = page.get("NextContinuationToken")
        token = next_value if isinstance(next_value, str) else None
        if not token:
            break


def _require_valid_gates(store: ObjectStore, manifest: dict[str, Any]) -> None:
    bucket = _required_env("CONFIGURATION_BUCKET")
    key_value = manifest.get("gateEvidenceKey", "gates/current.json")
    key = _string(key_value, "gateEvidenceKey")
    evidence = cast(object, json.loads(_read_body(store.get_object(Bucket=bucket, Key=key))))
    if not isinstance(evidence, dict):
        raise ValueError("gate evidence must be an object")
    gates = _object(cast(dict[str, Any], evidence).get("gates"))
    now = datetime.now(UTC)
    for gate_id in (f"GATE-{number:03d}" for number in range(1, 7)):
        record = _object(gates.get(gate_id))
        if record.get("decision") != "valid":
            raise ValueError(f"{gate_id} is not valid")
        expires_at = record.get("expiresAt")
        if isinstance(expires_at, str) and _parse_time(expires_at) <= now:
            raise ValueError(f"{gate_id} is expired")


def _require_gate(gate_id: str) -> None:
    store = cast(ObjectStore, boto3.client("s3"))
    bucket = _required_env("CONFIGURATION_BUCKET")
    evidence = cast(
        object,
        json.loads(
            _read_body(store.get_object(Bucket=bucket, Key="gates/current.json"))
        ),
    )
    if not isinstance(evidence, dict):
        raise ValueError("gate evidence must be an object")
    record = _object(_object(cast(dict[str, Any], evidence).get("gates")).get(gate_id))
    if record.get("decision") != "valid":
        raise ValueError(f"{gate_id} is not valid")
    expires_at = record.get("expiresAt")
    if isinstance(expires_at, str) and _parse_time(expires_at) <= datetime.now(UTC):
        raise ValueError(f"{gate_id} is expired")


def _latest_manifest(index: dict[str, Any], hashes: dict[str, str]) -> dict[str, Any]:
    latest: dict[str, Any] = {
        "schemaVersion": index["schemaVersion"],
        "releaseId": index["releaseId"],
        "releaseMode": index["releaseMode"],
        "generatedAt": index["generatedAt"],
        "normalizationVersion": index["normalizationVersion"],
        "indexPath": f"data/releases/{index['releaseId']}/index.json",
        "searchIndexPath": f"data/releases/{index['releaseId']}/search-index.json",
        "artifactHashes": hashes,
    }
    if index.get("releaseMode") == "normal":
        release_root = f"data/releases/{index['releaseId']}"
        latest.update(
            {
                "tagTaxonomyPath": f"{release_root}/tag-taxonomy.json",
                "tagIndexPath": f"{release_root}/tag-index.json",
                "tagAliasIndexPath": f"{release_root}/tag-alias-index.json",
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
    return latest


def _pseudonym_secret() -> bytes:
    arn = _required_env("PSEUDONYM_SECRET_ARN")
    response = cast(SecretStore, boto3.client("secretsmanager")).get_secret_value(SecretId=arn)
    return _string(response.get("SecretString"), "pseudonym secret").encode()


def _coverage(manifest: dict[str, Any]) -> Coverage:
    return Coverage(
        start=_string(manifest.get("coverageStart"), "coverageStart"),
        end=_string(manifest.get("coverageEnd"), "coverageEnd"),
        complete_from_start=manifest.get("completeFromStart") is True,
        source_updated_at=_string(manifest.get("sourceUpdatedAt"), "sourceUpdatedAt"),
    )


def _thread_comments(thread: dict[str, Any]) -> list[dict[str, Any]]:
    snippet = _object(thread.get("snippet"))
    top = snippet.get("topLevelComment")
    replies = _objects(_object(thread.get("replies")).get("comments"))
    replies.extend(_objects(thread.get("allReplies")))
    return ([cast(dict[str, Any], top)] if isinstance(top, dict) else []) + replies


def _objects(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        cast(dict[str, Any], item)
        for item in cast(list[object], value)
        if isinstance(item, dict)
    ]


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} is required")
    return value


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def _duration_seconds(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
    if match is None:
        return None
    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    return hours * 3600 + minutes * 60 + seconds


def _enqueue_child(
    parent: dict[str, Any],
    job_type: str,
    target_id: str,
    stage: str,
    manifest: dict[str, Any],
) -> None:
    from app.runtime.handlers import enqueue_job

    table = boto3.resource("dynamodb").Table(_required_env("CONTROL_TABLE"))
    queue = boto3.resource("sqs").Queue(_required_env("JOB_QUEUE_URL"))
    enqueue_job(
        {
            "jobType": job_type,
            "targetId": target_id,
            "inputVersion": f"{parent['inputVersion']}:{stage}",
            "inputManifest": manifest,
            "correlationId": parent.get("correlationId", parent.get("jobId")),
        },
        cast(Any, table),
        cast(Any, queue),
    )


def _record_quota(report: dict[str, Any], job: dict[str, Any], reserved: int) -> None:
    total = report.get("totalUnits")
    method_units: dict[str, int] = {}
    if isinstance(total, int):
        _emit_metric("YouTubeQuotaUnits", total, {"JobType": str(job.get("jobType", "unknown"))})
    for event in _objects(report.get("events")):
        units = event.get("units")
        method = event.get("method")
        if isinstance(units, int) and isinstance(method, str):
            method_units[method] = method_units.get(method, 0) + units
            _emit_metric("YouTubeQuotaUnitsByMethod", units, {"Method": method})
    table = _control_table()
    job_id = _string(job.get("jobId"), "jobId")
    table.update_item(
        Key={"pk": f"JOB#{job_id}", "sk": "EVENT#0001"},
        UpdateExpression="SET quotaUnitsByMethod = :methods, quotaUnitsTotal = :total",
        ExpressionAttributeValues={":methods": method_units, ":total": total or 0},
    )
    if isinstance(total, int) and total != reserved:
        table.update_item(
            Key=_quota_key(),
            UpdateExpression="ADD used :difference",
            ExpressionAttributeValues={":difference": total - reserved},
        )


def reserve_quota(job: dict[str, Any], units: int) -> int:
    table = _control_table()
    response = table.get_item(Key=_quota_key(), ConsistentRead=True)
    item = _object(response.get("Item"))
    used_value = item.get("used", 0)
    used = used_value if isinstance(used_value, int) else 0
    limit = int(os.environ.get("YOUTUBE_DAILY_QUOTA", "10000"))
    action = quota_action(
        _string(job.get("jobType"), "jobType"), QuotaBudget(limit, used), units
    )
    if action in {QuotaAction.STOP, QuotaAction.STOP_LOW_PRIORITY}:
        raise RuntimeError(f"quota policy stopped {job['jobType']}: {action.value}")
    table.update_item(
        Key=_quota_key(),
        UpdateExpression="SET updatedAt = :now ADD used :units",
        ConditionExpression="attribute_not_exists(used) OR used <= :remaining",
        ExpressionAttributeValues={
            ":now": _now(),
            ":units": units,
            ":remaining": limit - units,
        },
    )
    return units


def _quota_key() -> dict[str, str]:
    day = datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    return {"pk": f"QUOTA#{day}", "sk": "YOUTUBE"}


def _control_table() -> ControlTable:
    return cast(
        ControlTable, boto3.resource("dynamodb").Table(_required_env("CONTROL_TABLE"))
    )


def _emit_metric(name: str, value: int | float, dimensions: dict[str, str]) -> None:
    metrics = cast(Metrics, boto3.client("cloudwatch"))
    metrics.put_metric_data(
        Namespace="Diopside",
        MetricData=[
            {
                "MetricName": name,
                "Value": value,
                "Unit": "Count",
                "Dimensions": [
                    {"Name": key, "Value": dimension_value}
                    for key, dimension_value in sorted(dimensions.items())
                ],
            }
        ],
    )


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
