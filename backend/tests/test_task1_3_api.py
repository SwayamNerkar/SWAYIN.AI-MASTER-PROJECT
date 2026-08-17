import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_features_metadata_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/features/metadata")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "feature_name" in data[0]

@pytest.mark.asyncio
async def test_nifty_features_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/features/nifty?timeframe=1m&limit=40")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NIFTY"
    assert data["timeframe"] == "1m"
    assert "snapshots" in data
    assert len(data["snapshots"]) == 40
    last_snap = data["snapshots"][-1]
    assert "rsi_14" in last_snap["features"]

@pytest.mark.asyncio
async def test_sensex_features_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/features/sensex?timeframe=5m&limit=40")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SENSEX"
    assert data["timeframe"] == "5m"
    assert len(data["snapshots"]) == 40
