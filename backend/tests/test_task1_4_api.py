import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_nifty_regime_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/regime/nifty")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NIFTY"
    assert "directional_regime" in data
    assert "volatility_state" in data
    assert "confidence" in data
    assert "reasons" in data
    assert isinstance(data["reasons"], list)

@pytest.mark.asyncio
async def test_sensex_regime_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/regime/sensex")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SENSEX"
    assert "directional_regime" in data

@pytest.mark.asyncio
async def test_nifty_regime_history_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/regime/nifty/history?timeframe=1m&limit=40")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NIFTY"
    assert "snapshots" in data
    assert len(data["snapshots"]) > 0
