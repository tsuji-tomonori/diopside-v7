import httpx
import pytest

from app.collectors.youtube import YouTubeApiError, YouTubeDataClient


def test_videos_batches_at_fifty_and_records_quota() -> None:
    batch_sizes: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        ids = request.url.params["id"].split(",")
        batch_sizes.append(len(ids))
        return httpx.Response(200, json={"items": [{"id": value} for value in ids]})

    with YouTubeDataClient("secret", transport=httpx.MockTransport(handler)) as client:
        videos = list(client.videos([f"video-{index}" for index in range(101)]))

    assert len(videos) == 101
    assert batch_sizes == [50, 50, 1]
    assert client.quota_report()["totalUnits"] == 3


def test_non_retryable_reason_is_preserved_without_leaking_key() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(
            403,
            json={"error": {"errors": [{"reason": "quotaExceeded"}]}},
        )

    with YouTubeDataClient(
        "must-not-appear", transport=httpx.MockTransport(handler), sleep=lambda _value: None
    ) as client, pytest.raises(YouTubeApiError) as error:
        client.channel("channel")

    assert requests == 1
    assert error.value.reason == "quotaExceeded"
    assert "must-not-appear" not in str(error.value)


def test_retryable_status_is_retried() -> None:
    requests = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        if requests == 1:
            return httpx.Response(503, json={"error": {"status": "UNAVAILABLE"}})
        return httpx.Response(200, json={"items": []})

    with YouTubeDataClient(
        "secret", transport=httpx.MockTransport(handler), sleep=lambda _value: None
    ) as client:
        assert client.channel("channel") is None

    assert requests == 2
    assert len(client.quota_events) == 2
