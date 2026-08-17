import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["data_feed_mode"] == "MOCK"

@pytest.mark.asyncio
async def test_market_status_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/market/status")
    assert response.status_code == 200
    data = response.json()
    assert "state" in data
    assert data["market"] == "NSE/BSE"

@pytest.mark.asyncio
async def test_nifty_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/market/nifty")
    assert response.status_code == 200
    data = response.json()
    assert "quote" in data
    assert "ohlcv" in data
    assert data["quote"]["symbol"] == "NIFTY"

@pytest.mark.asyncio
async def test_nifty_options_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/options/nifty")
    assert response.status_code == 200
    data = response.json()
    assert data["underlying"] == "NIFTY"
    assert len(data["chain"]) > 0

@pytest.mark.asyncio
async def test_cost_calculate_endpoint():
    payload = {
        "symbol": "NIFTY24500CE",
        "entry_price": 180.0,
        "exit_price": 220.0,
        "quantity": 25
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/costs/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["gross_pnl"] == 1000.0
    assert data["net_pnl"] > 0
    assert data["is_profitable"] is True
