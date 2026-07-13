# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false

import httpx
import pytest

from app.main import app


@pytest.mark.anyio
async def test_health() -> None:
    """health endpointが準備完了を返すことを検証する。"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_latest_contract() -> None:
    """latest契約endpointが有効なrelease IDを返すことを検証する。"""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/contracts/latest")
    assert response.status_code == 200
    assert response.json()["releaseId"] == "20260711-001"
