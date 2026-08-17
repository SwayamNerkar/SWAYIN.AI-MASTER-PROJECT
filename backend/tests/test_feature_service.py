import datetime
import pytest
import pytz
from app.schemas.market_data import OHLCVCandle
from app.services.feature_service import feature_service

IST = pytz.timezone("Asia/Kolkata")

def make_test_candles(n: int = 35) -> list[OHLCVCandle]:
    base = datetime.datetime(2026, 8, 17, 9, 15, tzinfo=IST)
    res = []
    for i in range(n):
        res.append(OHLCVCandle(
            symbol="NIFTY",
            timestamp=base + datetime.timedelta(minutes=i),
            interval="1m",
            open=24500.0 + i,
            high=24510.0 + i,
            low=24495.0 + i,
            close=24505.0 + i,
            volume=10000 + i * 100
        ))
    return res

def test_feature_service_metadata():
    meta = feature_service.get_feature_metadata()
    assert len(meta) > 20
    names = [m.feature_name for m in meta]
    assert "rsi_14" in names
    assert "ema_21" in names
    assert "vwap" in names

def test_feature_series_generation_and_warmup():
    candles = make_test_candles(35)
    snapshots = feature_service.generate_feature_series(candles, timeframe="1m")
    assert len(snapshots) == 35
    
    # First snapshot (index 0) has insufficient warmup bars (< 30)
    assert snapshots[0].warmup_ready is False
    
    # Snapshot 34 (35 bars) satisfies warmup requirements
    assert snapshots[34].warmup_ready is True
    assert "rsi_14" in snapshots[34].features
    assert snapshots[34].features["rsi_14"] is not None

def test_generate_single_latest_features():
    candles = make_test_candles(35)
    snap = feature_service.generate_features(candles, timeframe="1m")
    assert snap.symbol == "NIFTY"
    assert snap.warmup_ready is True
    assert "price_change_pct" in snap.features
