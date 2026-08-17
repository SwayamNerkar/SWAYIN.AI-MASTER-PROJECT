import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_market_snapshot_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/market/snapshot")
    assert response.status_code == 200
    data = response.json()
    assert "nifty" in data
    assert "sensex" in data
    assert "data_health" in data
    assert data["nifty"]["symbol"] == "NIFTY"
    assert data["sensex"]["symbol"] == "SENSEX"
    assert data["data_health"]["validation_passed"] is True

@pytest.mark.asyncio
async def test_validated_nifty_options_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/options/nifty")
    assert response.status_code == 200
    data = response.json()
    assert data["underlying"] == "NIFTY"
    assert data["is_validated"] is True
    assert data["spot_price"] > 20000.0
