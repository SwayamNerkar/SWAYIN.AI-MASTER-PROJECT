import pytest
from app.adapters.mock.mock_feed import MockMarketDataAdapter

feed = MockMarketDataAdapter(seed=42)

@pytest.mark.asyncio
async def test_mock_index_quote():
    quote = await feed.get_index_quote("NIFTY")
    assert quote["symbol"] == "NIFTY"
    assert quote["ltp"] > 20000.0
    assert quote["is_simulated"] is True
    assert "MOCK" in quote["data_mode"]

@pytest.mark.asyncio
async def test_mock_ohlcv_generation():
    bars = await feed.get_ohlcv("NIFTY", timeframe="1m", limit=10)
    assert len(bars) == 10
    first_bar = bars[0]
    assert "open" in first_bar
    assert "high" in first_bar
    assert "low" in first_bar
    assert "close" in first_bar
    assert first_bar["high"] >= max(first_bar["open"], first_bar["close"])
    assert first_bar["low"] <= min(first_bar["open"], first_bar["close"])
