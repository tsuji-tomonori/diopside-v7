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
    """正規ジョブキーがバイト長を考慮し、安定することを検証する。"""
    # 1. 初期化
    job = ("normalize", "動画", "v1")

    # 2. テストの実行
    first = canonical_job_key(*job)
    second = canonical_job_key(*job)
    different = canonical_job_key("normalize", "動", "画v1")

    # 3. アサーション
    assert first == second
    assert first != different


def test_retry_policy_has_three_bounded_retries() -> None:
    """再試行ポリシーが上限付き3回の再試行を行うことを検証する。"""

    # 1. 初期化
    class FixedRandom:
        def __init__(self, ratio: float) -> None:
            self.ratio = ratio

        def uniform(self, low: float, high: float) -> float:
            return low + (high - low) * self.ratio

    zero = FixedRandom(0)
    one = FixedRandom(1)

    # 2. テストの実行
    zero_delays = [retry_delay_seconds(index, zero) for index in (1, 2, 3)]
    one_delays = [retry_delay_seconds(index, one) for index in (1, 2, 3)]
    capped_delay = retry_delay_seconds(1, zero, retry_after_seconds=5000)
    scheduled = retry_disposition(1, True)
    exhausted = retry_disposition(4, True)
    permanent = retry_disposition(1, False)

    # 3. アサーション
    assert zero_delays == [0, 0, 0]
    assert one_delays == [2, 4, 8]
    assert capped_delay == 3600
    assert scheduled == "scheduled"
    assert exhausted == "exhausted_to_dlq"
    assert permanent == "permanent_to_dlq"


def test_live_reservation_uses_at_least_eight_hours() -> None:
    """ライブ収集予約が最低8時間分を確保することを検証する。"""
    # 1. 初期化
    daily_limit = 10_000

    # 2. テストの実行
    short_reservation = live_chat_reservation_units(daily_limit, timedelta(hours=1))
    long_reservation = live_chat_reservation_units(daily_limit, timedelta(hours=10))

    # 3. アサーション
    assert short_reservation == 14_405
    assert long_reservation == 18_005


def test_quota_protects_compliance_and_live_work() -> None:
    """quota制御が規約対応処理とライブ処理を保護することを検証する。"""
    # 1. 初期化
    budget = QuotaBudget(daily_limit=10_000, used=9_500)

    # 2. テストの実行
    comment_action = quota_action("comment_full_refresh", budget, 1)
    live_action = quota_action("live_chat_collect", budget, 1)
    deletion_action = quota_action("deletion_refresh", budget, 1)

    # 3. アサーション
    assert comment_action == QuotaAction.STOP
    assert live_action == QuotaAction.WARN
    assert deletion_action == QuotaAction.WARN


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
    """データ分類ごとの保持期限境界を検証する。"""
    # 1. 初期化
    created = datetime(2026, 1, 1, tzinfo=UTC)

    # 2. テストの実行
    deadline = retention_deadline(data_class, created)
    before = must_delete(deadline, created + timedelta(days=days, seconds=-1))
    at = must_delete(deadline, created + timedelta(days=days))
    after = must_delete(deadline, created + timedelta(days=days, seconds=1))

    # 3. アサーション
    assert not before
    assert at
    assert after


def test_shorter_permission_or_gate_deadline_wins() -> None:
    """permissionまたはgateの短い期限を優先することを検証する。"""
    # 1. 初期化
    created = datetime(2026, 1, 1, tzinfo=UTC)
    explicit = created + timedelta(days=20)
    gate = created + timedelta(days=10)

    # 2. テストの実行
    deadline = retention_deadline(
        DataClass.REPLAY_CHAT, created, explicit_until=explicit, gate_until=gate
    )

    # 3. アサーション
    assert deadline == gate


def test_deletion_event_requires_every_layer_and_cdn() -> None:
    """削除イベントに全レイヤーとCDN指定が必須であることを検証する。"""
    # 1. 初期化
    required_layers = ("public", "processed", "raw")

    # 2. テストの実行
    with pytest.raises(ValueError) as layer_error:
        DeletionEvent("author", ("raw",), ("/*",), "operator", "now", "request")
    with pytest.raises(ValueError) as cdn_error:
        DeletionEvent("author", required_layers, (), "operator", "now", "request")

    # 3. アサーション
    assert "layers" in str(layer_error.value)
    assert "CDN" in str(cdn_error.value)
