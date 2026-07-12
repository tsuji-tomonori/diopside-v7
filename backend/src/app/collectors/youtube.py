from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

import httpx

MAX_BATCH_SIZE: Final = 50
RETRYABLE_STATUS: Final = frozenset({429, 500, 502, 503, 504})
QUOTA_UNITS: Final = {
    "channels.list": 1,
    "playlistItems.list": 1,
    "videos.list": 1,
    "commentThreads.list": 1,
    "comments.list": 1,
    "liveChatMessages.list": 5,
    "search.list": 100,
}


class YouTubeApiError(RuntimeError):
    def __init__(self, method: str, status: int, reason: str, retryable: bool) -> None:
        super().__init__(f"{method} failed: HTTP {status} ({reason})")
        self.method = method
        self.status = status
        self.reason = reason
        self.retryable = retryable


@dataclass(frozen=True)
class QuotaEvent:
    method: str
    units: int
    requested_ids: int
    status: int
    latency_ms: int
    retryable: bool
    reason: str | None = None
    request_id: str | None = None


class JsonCheckpoint:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {}
        value = cast(object, json.loads(self.path.read_text(encoding="utf-8")))
        if not isinstance(value, dict):
            raise ValueError("checkpoint root must be an object")
        return cast(dict[str, Any], value)

    def save(self, value: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        temporary.replace(self.path)


class YouTubeDataClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://www.googleapis.com/youtube/v3",
        timeout_seconds: float = 20.0,
        max_attempts: int = 5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not api_key:
            raise ValueError("YouTube API key is required")
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._max_attempts = max_attempts
        self._sleep = sleep
        self._http = httpx.Client(timeout=timeout_seconds, transport=transport)
        self.quota_events: list[QuotaEvent] = []

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> YouTubeDataClient:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def quota_report(self) -> dict[str, Any]:
        return {
            "totalUnits": sum(event.units for event in self.quota_events),
            "events": [asdict(event) for event in self.quota_events],
        }

    def _request(
        self,
        resource: str,
        method: str,
        params: dict[str, str | int],
        *,
        requested_ids: int = 0,
    ) -> dict[str, Any]:
        safe_params = {**params, "key": self._api_key}
        for attempt in range(self._max_attempts):
            started = time.monotonic()
            try:
                response = self._http.get(f"{self._base_url}/{resource}", params=safe_params)
            except (httpx.TimeoutException, httpx.NetworkError) as error:
                if attempt + 1 < self._max_attempts:
                    self._sleep(2**attempt)
                    continue
                raise YouTubeApiError(method, 0, type(error).__name__, True) from error

            latency_ms = round((time.monotonic() - started) * 1000)
            reason = _error_reason(response)
            retryable = response.status_code in RETRYABLE_STATUS
            self.quota_events.append(
                QuotaEvent(
                    method=method,
                    units=QUOTA_UNITS[method],
                    requested_ids=requested_ids,
                    status=response.status_code,
                    latency_ms=latency_ms,
                    retryable=retryable,
                    reason=reason,
                    request_id=response.headers.get("x-goog-request-id"),
                )
            )
            if response.is_success:
                payload = cast(object, response.json())
                if not isinstance(payload, dict):
                    raise YouTubeApiError(method, response.status_code, "invalidResponse", False)
                return cast(dict[str, Any], payload)
            if retryable and attempt + 1 < self._max_attempts:
                self._sleep(2**attempt)
                continue
            raise YouTubeApiError(method, response.status_code, reason or "unknown", retryable)
        raise AssertionError("retry loop exhausted")

    def channel(self, channel_id: str) -> dict[str, Any] | None:
        payload = self._request(
            "channels",
            "channels.list",
            {"part": "snippet,contentDetails", "id": channel_id, "maxResults": 1},
            requested_ids=1,
        )
        items = _object_items(payload)
        return items[0] if items else None

    def discover_channel(self, query: str, max_results: int = 5) -> list[dict[str, Any]]:
        """Explicit discovery only; normal channel polling must not call search.list."""
        payload = self._request(
            "search",
            "search.list",
            {
                "part": "snippet",
                "q": query,
                "type": "channel",
                "maxResults": min(max_results, 50),
            },
        )
        return _object_items(payload)

    def uploads(
        self, playlist_id: str, checkpoint: JsonCheckpoint | None = None
    ) -> Iterator[dict[str, Any]]:
        state = checkpoint.load() if checkpoint else {}
        page_token = state.get("nextPageToken")
        while True:
            params: dict[str, str | int] = {
                "part": "snippet,contentDetails,status",
                "playlistId": playlist_id,
                "maxResults": 50,
            }
            if isinstance(page_token, str) and page_token:
                params["pageToken"] = page_token
            payload = self._request("playlistItems", "playlistItems.list", params)
            yield from _object_items(payload)
            next_token = payload.get("nextPageToken")
            page_token = next_token if isinstance(next_token, str) else None
            if checkpoint:
                checkpoint.save({"nextPageToken": page_token, "complete": page_token is None})
            if page_token is None:
                break

    def videos(self, video_ids: Sequence[str]) -> Iterator[dict[str, Any]]:
        unique_ids = list(dict.fromkeys(video_ids))
        for batch in _chunks(unique_ids, MAX_BATCH_SIZE):
            payload = self._request(
                "videos",
                "videos.list",
                {
                    "part": "snippet,contentDetails,liveStreamingDetails,status,statistics",
                    "id": ",".join(batch),
                    "maxResults": len(batch),
                },
                requested_ids=len(batch),
            )
            yield from _object_items(payload)

    def comments(self, video_id: str) -> Iterator[dict[str, Any]]:
        page_token: str | None = None
        while True:
            params: dict[str, str | int] = {
                "part": "snippet,replies",
                "videoId": video_id,
                "maxResults": 100,
                "order": "time",
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token
            payload = self._request(
                "commentThreads", "commentThreads.list", params, requested_ids=1
            )
            for thread in _object_items(payload):
                yield thread
                snippet = _object(thread.get("snippet"))
                total_replies_value = snippet.get("totalReplyCount", 0)
                total_replies = total_replies_value if isinstance(total_replies_value, int) else 0
                embedded = _object(thread.get("replies"))
                embedded_items_value = embedded.get("comments", [])
                embedded_items = (
                    cast(list[object], embedded_items_value)
                    if isinstance(embedded_items_value, list)
                    else []
                )
                if total_replies > len(embedded_items):
                    top = _object(snippet.get("topLevelComment"))
                    parent_id = top.get("id")
                    if isinstance(parent_id, str):
                        thread["allReplies"] = list(self.comment_replies(parent_id))
            token = payload.get("nextPageToken")
            page_token = token if isinstance(token, str) else None
            if page_token is None:
                break

    def comment_replies(self, parent_id: str) -> Iterator[dict[str, Any]]:
        page_token: str | None = None
        while True:
            params: dict[str, str | int] = {
                "part": "snippet",
                "parentId": parent_id,
                "maxResults": 100,
                "textFormat": "plainText",
            }
            if page_token:
                params["pageToken"] = page_token
            payload = self._request("comments", "comments.list", params, requested_ids=1)
            yield from _object_items(payload)
            token = payload.get("nextPageToken")
            page_token = token if isinstance(token, str) else None
            if page_token is None:
                break

    def live_chat_page(self, live_chat_id: str, page_token: str | None = None) -> dict[str, Any]:
        params: dict[str, str | int] = {
            "part": "id,snippet,authorDetails",
            "liveChatId": live_chat_id,
            "maxResults": 2000,
        }
        if page_token:
            params["pageToken"] = page_token
        return self._request(
            "liveChat/messages", "liveChatMessages.list", params, requested_ids=1
        )


def _chunks(values: list[str], size: int) -> Iterator[list[str]]:
    for start in range(0, len(values), size):
        yield values[start : start + size]


def _object_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items = cast(object, payload.get("items", []))
    if not isinstance(items, list):
        return []
    object_items = cast(list[object], items)
    return [_object(cast(object, item)) for item in object_items if isinstance(item, dict)]


def _object(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return cast(dict[str, Any], value)


def _error_reason(response: httpx.Response) -> str | None:
    try:
        payload = cast(object, response.json())
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    payload_object = cast(dict[str, Any], payload)
    error = _object(payload_object.get("error"))
    errors = cast(object, error.get("errors"))
    if isinstance(errors, list) and errors and isinstance(errors[0], dict):
        reason = _object(cast(object, errors[0])).get("reason")
        return reason if isinstance(reason, str) else None
    status = error.get("status")
    return status if isinstance(status, str) else None
