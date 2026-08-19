import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_run_backtest_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        payload = {
            "symbol": "NIFTY",
            "timeframe": "1m",
            "model_version": "v1.0.0",
            "horizon_bars": 3,
            "walk_forward_mode": "EXPANDING",
            "initial_train_bars": 70,
            "eval_window_bars": 10
        }
        response = await ac.post("/api/v1/backtest/run", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "backtest_id" in data
    assert data["status"] == "COMPLETED"
    assert "overall_metrics" in data
    assert "regime_metrics" in data
    assert "volatility_metrics" in data
    
    b_id = data["backtest_id"]
    
    # Test GET /api/v1/backtest
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_list = await ac.get("/api/v1/backtest")
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 1
    
    # Test GET /api/v1/backtest/{id}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_get = await ac.get(f"/api/v1/backtest/{b_id}")
    assert res_get.status_code == 200
    assert res_get.json()["backtest_id"] == b_id

    # Test GET /api/v1/backtest/{id}/predictions
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_preds = await ac.get(f"/api/v1/backtest/{b_id}/predictions?limit=10")
    assert res_preds.status_code == 200
    assert len(res_preds.json()["predictions"]) <= 10
