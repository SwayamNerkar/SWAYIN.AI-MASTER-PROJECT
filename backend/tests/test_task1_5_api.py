import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_nifty_prediction_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/prediction/nifty")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NIFTY"
    assert "predicted_value" in data
    assert "prediction_target" in data
    assert data["data_mode"] == "MOCK / SIMULATED DATA"

@pytest.mark.asyncio
async def test_sensex_prediction_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/prediction/sensex")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "SENSEX"
    assert "predicted_value" in data

@pytest.mark.asyncio
async def test_train_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/prediction/train?symbol=NIFTY&timeframe=1m&horizon=3")
    assert response.status_code == 200
    data = response.json()
    assert data["symbol"] == "NIFTY"
    assert "metrics" in data
    assert "improves_naive" in data["metrics"]
