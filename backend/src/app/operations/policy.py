from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Final, Literal, Protocol


class JobType(StrEnum):
    METADATA_SYNC = "metadata_sync"
    LIVE_CHAT_COLLECT = "live_chat_collect"
    REPLAY_CHAT_IMPORT = "replay_chat_import"
    COMMENT_COLLECT = "comment_collect"
    NORMALIZE = "normalize"
    AGGREGATE = "aggregate"
    WORDCLOUD = "wordcloud"
    STATIC_EXPORT = "static_export"


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED_RETRYABLE = "failed_retryable"
    FAILED_PERMANENT = "failed_permanent"
    CANCELLED = "cancelled"


def canonical_job_key(job_type: str, target_id: str, input_version: str) -> str:
    payload = bytearray()
    for value in (job_type, target_id, input_version):
        encoded = value.encode()
        if len(encoded) > 0xFFFFFFFF:
            raise ValueError("canonical job key field exceeds uint32 byte length")
        payload.extend(struct.pack(">I", len(encoded)))
        payload.extend(encoded)
    return hashlib.sha256(payload).hexdigest()


class UniformRandom(Protocol):
    def uniform(self, low: float, high: float) -> float: ...


def retry_delay_seconds(
    retry_ordinal: int,
    random: UniformRandom,
    retry_after_seconds: float | None = None,
) -> float:
    if retry_ordinal not in {1, 2, 3}:
        raise ValueError("retry ordinal must be 1..3")
    upper = min(8.0, 2.0 * (2 ** (retry_ordinal - 1)))
    delay = random.uniform(0, upper)
    if retry_after_seconds is not None:
        floor = min(3600.0, max(1.0, retry_after_seconds))
        delay = max(delay, floor)
    return min(delay, 3600.0)


def retry_disposition(
    attempt: int, retryable: bool
) -> Literal["scheduled", "exhausted_to_dlq", "permanent_to_dlq"]:
    if not retryable:
        return "permanent_to_dlq"
    return "scheduled" if attempt < 4 else "exhausted_to_dlq"


@dataclass(frozen=True)
class QuotaBudget:
    daily_limit: int
    used: int
    reserved_live: int = 0

    @property
    def ratio(self) -> float:
        return (self.used + self.reserved_live) / self.daily_limit

    def can_spend(self, units: int) -> bool:
        return self.used + self.reserved_live + units <= self.daily_limit


def live_chat_reservation_units(
    polling_interval_ms: int,
    expected_remaining: timedelta | None,
    *,
    units_per_request: int = 5,
) -> int:
    if polling_interval_ms <= 0:
        raise ValueError("polling interval must be positive")
    minimum = timedelta(hours=8)
    horizon = max(expected_remaining or minimum, minimum)
    requests = int(horizon.total_seconds() * 1000 // polling_interval_ms) + 1
    return requests * units_per_request


class QuotaAction(StrEnum):
    CONTINUE = "continue"
    WARN = "warn"
    STOP_LOW_PRIORITY = "stop_low_priority"
    STOP = "stop"


PROTECTED_QUOTA_JOBS: Final = frozenset(
    {
        "deletion_refresh",
        "compliance_refresh_urgent",
        "live_start_check",
        JobType.LIVE_CHAT_COLLECT.value,
    }
)
LOW_PRIORITY_QUOTA_JOBS: Final = frozenset(
    {
        "comment_full_refresh",
        "comment_incremental",
        "metadata_refresh",
        JobType.COMMENT_COLLECT.value,
        JobType.METADATA_SYNC.value,
    }
)


def quota_action(job_type: str, budget: QuotaBudget, requested_units: int) -> QuotaAction:
    if job_type in PROTECTED_QUOTA_JOBS:
        return QuotaAction.WARN if budget.ratio >= 0.8 else QuotaAction.CONTINUE
    projected = (budget.used + budget.reserved_live + requested_units) / budget.daily_limit
    if projected >= 0.95:
        return QuotaAction.STOP
    if projected >= 0.8:
        return (
            QuotaAction.STOP_LOW_PRIORITY
            if job_type in LOW_PRIORITY_QUOTA_JOBS
            else QuotaAction.WARN
        )
    return QuotaAction.CONTINUE


class DataClass(StrEnum):
    API_DATA = "api_data"
    RAW_PROCESSED_VERSION = "raw_processed_version"
    REPLAY_CHAT = "replay_chat"
    PUBLIC_OLD_RELEASE = "public_old_release"
    OPERATIONAL_RECORD = "operational_record"


def retention_deadline(
    data_class: DataClass,
    created_at: datetime,
    *,
    explicit_until: datetime | None = None,
    gate_until: datetime | None = None,
) -> datetime:
    created_at = created_at.astimezone(UTC)
    defaults = {
        DataClass.API_DATA: timedelta(days=30),
        DataClass.RAW_PROCESSED_VERSION: timedelta(days=30),
        DataClass.REPLAY_CHAT: timedelta(days=30),
        DataClass.PUBLIC_OLD_RELEASE: timedelta(days=90),
        DataClass.OPERATIONAL_RECORD: timedelta(days=400),
    }
    deadline = created_at + defaults[data_class]
    candidates = [value.astimezone(UTC) for value in (explicit_until, gate_until) if value]
    return min([deadline, *candidates]) if candidates else deadline


def must_delete(deadline: datetime, now: datetime) -> bool:
    return now.astimezone(UTC) >= deadline.astimezone(UTC)


@dataclass(frozen=True)
class DeletionEvent:
    target_identity: str
    layers: tuple[str, ...]
    cdn_paths: tuple[str, ...]
    actor: str
    occurred_at: str
    reason: str

    def __post_init__(self) -> None:
        required_layers = {"public", "processed", "raw"}
        if not required_layers.issubset(self.layers):
            raise ValueError("deletion must cover public, processed, and raw layers")
        if not self.cdn_paths:
            raise ValueError("deletion must include CDN invalidation paths")
