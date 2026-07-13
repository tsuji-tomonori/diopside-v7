# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false

import httpx
import pytest

from app.main import app


@pytest.mark.anyio
async def test_health() -> None:
    """health endpointが準備完了を返すことを検証する。"""
    # 1. 初期化
    transport = httpx.ASGITransport(app=app)

    # 2. テストの実行
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")

    # 3. アサーション
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_latest_contract() -> None:
    """latest契約endpointが有効なrelease IDを返すことを検証する。"""
    # 1. 初期化
    transport = httpx.ASGITransport(app=app)

    # 2. テストの実行
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/contracts/latest")

    # 3. アサーション
    assert response.status_code == 200
    assert response.json()["releaseId"] == "20260711-001"
