from __future__ import annotations

import hashlib
import hmac
import html
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Final, Literal, cast

ALGORITHM_VERSION: Final = "normalize-v1/tokenizer-v1/aggregate-v1"
TOKENIZER_VERSION: Final = f"unicode-{unicodedata.unidata_version}/nfkc-regex-v1"
URL_PATTERN: Final = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
TOKEN_PATTERN: Final = re.compile(r"[一-龠々〆ヵヶぁ-んァ-ヶー]{2,}|[A-Za-z][A-Za-z0-9_-]{1,}")
CONTROL_PATTERN: Final = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
STOPWORDS: Final = frozenset({"これ", "それ", "あれ", "です", "ます", "する", "いる", "ある"})
PRIVATE_FIELDS: Final = frozenset(
    {"authorChannelId", "authorDisplayName", "authorDedupToken", "messageText", "amountMicros"}
)


class ProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class Coverage:
    start: str
    end: str
    complete_from_start: bool
    source_updated_at: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "coverageStart": self.start,
            "coverageEnd": self.end,
            "completeFromStart": self.complete_from_start,
            "sourceUpdatedAt": self.source_updated_at,
        }


def normalize_metadata(item: dict[str, Any], fetched_at: str) -> dict[str, Any]:
    snippet = _object(item.get("snippet"))
    details = _object(item.get("contentDetails"))
    status = _object(item.get("status"))
    live = _object(item.get("liveStreamingDetails"))
    statistics = _object(item.get("statistics"))
    video_id = _required(item, "id")
    result: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "videoId": video_id,
        "channelId": _required(snippet, "channelId"),
        "title": _required(snippet, "title"),
        "description": _optional_string(snippet.get("description")) or "",
        "publishedAt": _optional_string(snippet.get("publishedAt")),
        "duration": _optional_string(details.get("duration")),
        "liveBroadcastContent": _optional_string(snippet.get("liveBroadcastContent")),
        "privacyStatus": _optional_string(status.get("privacyStatus")),
        "embeddable": (
            status.get("embeddable") if isinstance(status.get("embeddable"), bool) else None
        ),
        "sourceTags": _strings(snippet.get("tags")),
        "youtubeCategoryId": _optional_string(snippet.get("categoryId")),
        "etag": _optional_string(item.get("etag")),
        "fetchedAt": fetched_at,
    }
    for source_key, target_key in (
        ("scheduledStartTime", "scheduledStartTime"),
        ("actualStartTime", "actualStartTime"),
        ("actualEndTime", "actualEndTime"),
        ("activeLiveChatId", "activeLiveChatId"),
    ):
        result[target_key] = _optional_string(live.get(source_key))
    for source_key, target_key in (
        ("viewCount", "viewCount"),
        ("likeCount", "likeCount"),
        ("commentCount", "commentCount"),
    ):
        value = statistics.get(source_key)
        result[target_key] = int(value) if isinstance(value, str) and value.isdigit() else None
    thumbnails = _object(snippet.get("thumbnails"))
    preferred = _object(
        thumbnails.get("maxres") or thumbnails.get("high") or thumbnails.get("default")
    )
    result["thumbnail"] = (
        {
            "url": _required(preferred, "url"),
            "width": preferred.get("width"),
            "height": preferred.get("height"),
        }
        if preferred
        else None
    )
    return {key: value for key, value in result.items() if value is not None}


def classify_video_state(
    metadata: dict[str, Any],
) -> Literal["upcoming", "live", "archive", "unavailable"]:
    if metadata.get("privacyStatus") not in {None, "public", "unlisted"}:
        return "unavailable"
    broadcast = metadata.get("liveBroadcastContent")
    if broadcast == "upcoming":
        return "upcoming"
    if broadcast == "live" or (
        metadata.get("actualStartTime") and not metadata.get("actualEndTime")
    ):
        return "live"
    if metadata.get("duration"):
        return "archive"
    return "unavailable"


def normalize_chat_message(
    item: dict[str, Any], video_id: str, stream_started_at: datetime, secret: bytes
) -> dict[str, Any]:
    snippet = _object(item.get("snippet"))
    author = _object(item.get("authorDetails"))
    message_id = _required(item, "id")
    published_at = _required(snippet, "publishedAt")
    published = _parse_time(published_at)
    message_type = _optional_string(snippet.get("type")) or "unknown"
    event_type, paid_kind = _chat_type(message_type)
    display = _optional_string(snippet.get("displayMessage"))
    author_id = _optional_string(author.get("channelId"))
    record: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "sourceType": "youtube_live_chat",
        "sourceId": message_id,
        "videoId": video_id,
        "eventAt": published_at,
        "relativeSec": max(0, int((published - stream_started_at).total_seconds())),
        "text": normalize_text(display) if display else None,
        "eventType": event_type,
        "paidKind": paid_kind,
        "authorDedupToken": author_token(secret, video_id, author_id) if author_id else None,
    }
    paid = _object(snippet.get("superChatDetails") or snippet.get("superStickerDetails"))
    amount = paid.get("amountMicros")
    record["amountMicros"] = int(amount) if isinstance(amount, str) and amount.isdigit() else None
    record["currency"] = _optional_string(paid.get("currency"))
    return {key: value for key, value in record.items() if value is not None}


def normalize_comment(item: dict[str, Any], video_id: str, secret: bytes) -> dict[str, Any]:
    snippet = _object(item.get("snippet"))
    comment_id = _required(item, "id")
    author_id = _optional_string(snippet.get("authorChannelId"))
    if not author_id:
        channel = _object(snippet.get("authorChannelId"))
        author_id = _optional_string(channel.get("value"))
    text = _optional_string(snippet.get("textOriginal") or snippet.get("textDisplay"))
    return {
        "schemaVersion": "1.0.0",
        "sourceType": "youtube_comment",
        "sourceId": comment_id,
        "videoId": video_id,
        "eventAt": _required(snippet, "publishedAt"),
        "text": normalize_text(text) if text else None,
        "eventType": "comment",
        **({"authorDedupToken": author_token(secret, video_id, author_id)} if author_id else {}),
    }


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = URL_PATTERN.sub(" ", value)
    value = CONTROL_PATTERN.sub("", value)
    return re.sub(r"\s+", " ", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def tokenize(value: str) -> list[str]:
    return [
        token.casefold()
        for token in TOKEN_PATTERN.findall(normalize_text(value))
        if token.casefold() not in STOPWORDS and not token.isdigit()
    ]


def author_token(secret: bytes, video_id: str, author_id: str) -> str:
    video_key = hmac.new(secret, video_id.encode(), hashlib.sha256).digest()
    return hmac.new(video_key, author_id.encode(), hashlib.sha256).hexdigest()


def aggregate_events(
    events: list[dict[str, Any]],
    source: Literal["chat", "comments"],
    coverage: Coverage,
    generated_at: str,
) -> dict[str, Any]:
    terms: Counter[str] = Counter()
    authors: set[str] = set()
    timeline: Counter[int | str] = Counter()
    paid_count = 0
    for event in events:
        text = event.get("text")
        if isinstance(text, str):
            terms.update(tokenize(text))
        token = event.get("authorDedupToken")
        if isinstance(token, str):
            authors.add(token)
        if source == "chat":
            relative = event.get("relativeSec")
            if isinstance(relative, int):
                timeline[(relative // 60) * 60] += 1
            if event.get("paidKind"):
                paid_count += 1
        else:
            event_at = event.get("eventAt")
            if isinstance(event_at, str):
                timeline[event_at[:10]] += 1
    result: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "source": source,
        "totalCount": len(events),
        "uniqueAuthorsApprox": len(authors),
        "topTerms": [{"term": term, "count": count} for term, count in terms.most_common(100)],
        "timeline": [{"at": key, "count": count} for key, count in sorted(timeline.items())],
        "coverage": coverage.public_dict(),
        "generatedAt": generated_at,
        "algorithmVersion": ALGORITHM_VERSION,
        "tokenizerVersion": TOKENIZER_VERSION,
    }
    if source == "chat":
        result["paidEventCount"] = paid_count
    assert_public(result)
    return result


def wordcloud_artifact(
    video_id: str,
    source: Literal["chat", "comments", "both"],
    aggregate: dict[str, Any],
    coverage: Coverage,
    generated_at: str,
    *,
    minimum_terms: int = 3,
) -> tuple[dict[str, Any], str | None]:
    raw_terms = aggregate.get("topTerms", [])
    terms = cast(list[dict[str, Any]], raw_terms) if isinstance(raw_terms, list) else []
    metadata: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "videoId": video_id,
        "sourceSet": [source],
        "coverage": coverage.public_dict(),
        "tokenizerVersion": TOKENIZER_VERSION,
        "stopwordVersion": f"sha256:{hashlib.sha256(canonical_stopwords()).hexdigest()}",
        "algorithmVersion": ALGORITHM_VERSION,
        "generatedAt": generated_at,
    }
    if len(terms) < minimum_terms:
        return {
            **metadata,
            "status": "not_generated",
            "notGeneratedReason": "insufficient_terms",
        }, None
    selected = terms[:40]
    svg = _wordcloud_svg(selected)
    svg_hash = hashlib.sha256(svg.encode()).hexdigest()
    path = f"releases/{{releaseId}}/wordcloud/{video_id}-{source}.svg"
    return {
        **metadata,
        "status": "generated",
        "topTerms": selected,
        "svgPath": path,
        "svgSha256": svg_hash,
    }, svg


def timestamp_candidates(
    video_id: str,
    aggregate: dict[str, Any],
    duration_sec: int,
    coverage: Coverage,
    generated_at: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    if duration_sec < 0:
        raise ProcessingError("duration_sec must be non-negative")
    timeline = [
        item
        for item in _objects(aggregate.get("timeline"))
        if isinstance(item.get("at"), int)
        and isinstance(item.get("count"), int)
        and cast(int, item["at"]) <= duration_sec
    ]
    maximum = max((cast(int, item["count"]) for item in timeline), default=0)
    ranked = sorted(
        timeline,
        key=lambda item: (-cast(int, item["count"]), cast(int, item["at"])),
    )[:limit]
    items: list[dict[str, Any]] = []
    for item in sorted(ranked, key=lambda value: cast(int, value["at"])):
        at_sec = cast(int, item["at"])
        count = cast(int, item["count"])
        identity = f"{video_id}\0{at_sec}\0{ALGORITHM_VERSION}".encode()
        items.append(
            {
                "candidateId": f"ts_{hashlib.sha256(identity).hexdigest()[:20]}",
                "videoId": video_id,
                "atSec": at_sec,
                "label": "chat activity peak",
                "evidenceType": "chat_volume",
                "confidence": round(count / maximum, 4) if maximum else 0.0,
                "coverage": coverage.public_dict(),
                "algorithmVersion": ALGORITHM_VERSION,
            }
        )
    result = {
        "schemaVersion": "1.0.0",
        "videoId": video_id,
        "status": "generated" if items else "not_generated",
        "source": "chat_volume",
        "generatedAt": generated_at,
        "coverage": coverage.public_dict(),
        "algorithmVersion": ALGORITHM_VERSION,
        "items": items,
    }
    assert_public(result)
    return result


def assert_public(value: object) -> None:
    def visit(item: object) -> None:
        if isinstance(item, dict):
            for key, child in cast(dict[object, object], item).items():
                if key in PRIVATE_FIELDS:
                    raise ProcessingError(f"private field in public output: {key}")
                visit(child)
        elif isinstance(item, list):
            for child in cast(list[object], item):
                visit(child)

    visit(value)


def canonical_stopwords() -> bytes:
    return "\n".join(sorted(STOPWORDS)).encode()


def _wordcloud_svg(terms: list[dict[str, Any]]) -> str:
    elements: list[str] = []
    maximum = max(cast(int, item["count"]) for item in terms)
    for index, item in enumerate(terms):
        count = cast(int, item["count"])
        size = 14 + round(34 * count / maximum)
        x = 20 + (index % 4) * 150
        y = 35 + (index // 4) * 50
        elements.append(
            f'<text x="{x}" y="{y}" font-size="{size}" fill="#211d2b">'
            f"{html.escape(cast(str, item['term']))}</text>"
        )
    height = 70 + ((len(terms) - 1) // 4) * 50
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="640" height="{height}" '
        f'viewBox="0 0 640 {height}" role="img">' + "".join(elements) + "</svg>"
    )


def _chat_type(value: str) -> tuple[str, str | None]:
    mapping = {
        "textMessageEvent": ("message", None),
        "superChatEvent": ("paid", "super_chat"),
        "superStickerEvent": ("paid", "super_sticker"),
        "memberMilestoneChatEvent": ("membership", "milestone"),
        "membershipGiftingEvent": ("membership", "gift"),
        "giftMembershipReceivedEvent": ("membership", "gift_received"),
        "messageDeletedEvent": ("moderation", "deleted"),
        "userBannedEvent": ("moderation", "banned"),
        "pollEvent": ("poll", None),
    }
    return mapping.get(value, ("unknown", None))


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(UTC)


def _object(value: object) -> dict[str, Any]:
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def _objects(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [
        cast(dict[str, Any], item) for item in cast(list[object], value) if isinstance(item, dict)
    ]


def _required(value: dict[str, Any], key: str) -> str:
    result = value.get(key)
    if not isinstance(result, str) or not result:
        raise ProcessingError(f"missing {key}")
    return result


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in cast(list[object], value) if isinstance(item, str)]
