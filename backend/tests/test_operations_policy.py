from datetime import UTC, datetime, timedelta

import pytest

from app.operations.policy import (
    DataClass,
    DeletionEvent,
    QuotaAction,
    QuotaBudget,
    canonical_job_key,
    live_chat_reservation_units,
    must_delete,
    quota_action,
    retention_deadline,
    retry_delay_seconds,
    retry_disposition,
)


def test_canonical_job_key_is_byte_length_aware_and_stable() -> None:
    assert canonical_job_key("normalize", "動画", "v1") == canonical_job_key(
        "normalize", "動画", "v1"
    )
    assert canonical_job_key("normalize", "動画", "v1") != canonical_job_key(
        "normalize", "動", "画v1"
    )


def test_retry_policy_has_three_bounded_retries() -> None:
    class FixedRandom:
        def __init__(self, ratio: float) -> None:
            self.ratio = ratio

        def uniform(self, low: float, high: float) -> float:
            return low + (high - low) * self.ratio

    zero = FixedRandom(0)
    one = FixedRandom(1)
    assert [retry_delay_seconds(index, zero) for index in (1, 2, 3)] == [0, 0, 0]
    assert [retry_delay_seconds(index, one) for index in (1, 2, 3)] == [2, 4, 8]
    assert retry_delay_seconds(1, zero, retry_after_seconds=5000) == 3600
    assert retry_disposition(1, True) == "scheduled"
    assert retry_disposition(4, True) == "exhausted_to_dlq"
    assert retry_disposition(1, False) == "permanent_to_dlq"


def test_live_reservation_uses_at_least_eight_hours() -> None:
    assert live_chat_reservation_units(10_000, timedelta(hours=1)) == 14_405
    assert live_chat_reservation_units(10_000, timedelta(hours=10)) == 18_005


def test_quota_protects_compliance_and_live_work() -> None:
    budget = QuotaBudget(daily_limit=10_000, used=9_500)
    assert quota_action("comment_full_refresh", budget, 1) == QuotaAction.STOP
    assert quota_action("live_chat_collect", budget, 1) == QuotaAction.WARN
    assert quota_action("deletion_refresh", budget, 1) == QuotaAction.WARN


@pytest.mark.parametrize(
    ("data_class", "days"),
    [
        (DataClass.API_DATA, 30),
        (DataClass.RAW_PROCESSED_VERSION, 30),
        (DataClass.REPLAY_CHAT, 30),
        (DataClass.PUBLIC_OLD_RELEASE, 90),
        (DataClass.OPERATIONAL_RECORD, 400),
    ],
)
def test_retention_boundaries(data_class: DataClass, days: int) -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    deadline = retention_deadline(data_class, created)
    assert not must_delete(deadline, created + timedelta(days=days, seconds=-1))
    assert must_delete(deadline, created + timedelta(days=days))
    assert must_delete(deadline, created + timedelta(days=days, seconds=1))


def test_shorter_permission_or_gate_deadline_wins() -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    explicit = created + timedelta(days=20)
    gate = created + timedelta(days=10)
    assert (
        retention_deadline(DataClass.REPLAY_CHAT, created, explicit_until=explicit, gate_until=gate)
        == gate
    )


def test_deletion_event_requires_every_layer_and_cdn() -> None:
    with pytest.raises(ValueError, match="layers"):
        DeletionEvent("author", ("raw",), ("/*",), "operator", "now", "request")
    with pytest.raises(ValueError, match="CDN"):
        DeletionEvent("author", ("public", "processed", "raw"), (), "operator", "now", "request")
