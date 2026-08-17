import pytest
from app.engines.cost_engine import ProfitabilityCostEngine

cost_engine = ProfitabilityCostEngine()

def test_cost_calculation():
    # Buy 1 lot NIFTY CE at 180, Sell at 220 (Quantity = 25)
    result = cost_engine.calculate_trade_cost(
        symbol="NIFTY24500CE",
        entry_price=180.0,
        exit_price=220.0,
        quantity=25
    )

    assert result.buy_turnover == 4500.0  # 180 * 25
    assert result.sell_turnover == 5500.0 # 220 * 25
    assert result.gross_pnl == 1000.0     # 5500 - 4500
    assert result.brokerage == 40.0       # 20 * 2 orders
    assert result.stt > 0
    assert result.gst > 0
    assert result.total_charges > 40.0
    assert result.net_pnl == round(1000.0 - result.total_charges, 2)
    assert result.is_profitable is True

def test_unprofitable_trade_cost():
    # Loss trade: Buy at 180, Sell at 160 (Quantity = 25)
    result = cost_engine.calculate_trade_cost(
        symbol="NIFTY24500CE",
        entry_price=180.0,
        exit_price=160.0,
        quantity=25
    )

    assert result.gross_pnl == -500.0
    assert result.net_pnl < -500.0
    assert result.is_profitable is False
