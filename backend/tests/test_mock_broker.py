import pytest
from app.adapters.mock.mock_broker import MockBrokerAdapter

broker = MockBrokerAdapter(initial_capital=20000.0)

@pytest.mark.asyncio
async def test_account_info():
    info = await broker.get_account_info()
    assert info["mode"] == "PAPER_TRADING"
    assert info["available_capital"] == 20000.0

@pytest.mark.asyncio
async def test_paper_order_execution():
    # Place valid paper order
    res = await broker.place_order({
        "symbol": "NIFTY24500CE",
        "side": "BUY",
        "quantity": 25,
        "price": 180.0
    })
    assert res["status"] == "FILLED"
    assert res["is_mock"] is True
    
    cap = await broker.get_available_capital()
    assert cap == 20000.0 - (180.0 * 25)

@pytest.mark.asyncio
async def test_insufficient_funds_rejection():
    # Attempt to place order exceeding capital
    res = await broker.place_order({
        "symbol": "SENSEX80000CE",
        "side": "BUY",
        "quantity": 500,
        "price": 500.0
    })
    assert res["status"] == "REJECTED"
    assert "Insufficient paper capital" in res["reason"]
