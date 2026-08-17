import datetime
import pytest
import numpy as np
import pytz
from app.schemas.market_data import OHLCVCandle
from app.services.feature_service import feature_service
from app.services.regime_service import regime_service
from app.engines.regime_engine import MarketRegimeEngine, DirectionalRegime

IST = pytz.timezone("Asia/Kolkata")

def generate_trend_candles(count: int = 70) -> list[OHLCVCandle]:
    base_time = datetime.datetime(2026, 8, 17, 9, 15, tzinfo=IST)
    candles = []
    np.random.seed(42)
    c = 24500.0
    for i in range(count):
        t = base_time + datetime.timedelta(minutes=i)
        c += np.random.uniform(4, 10) # Strong upward trend for ADX & EMA warmup
        o = c - np.random.uniform(0, 1)
        h = max(o, c) + np.random.uniform(0, 2)
        l = min(o, c) - np.random.uniform(0, 1)
        v = int(np.random.uniform(10000, 50000))
        candles.append(OHLCVCandle(
            symbol="NIFTY",
            timestamp=t,
            interval="1m",
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(c, 2),
            volume=v
        ))
    return candles

def test_regime_stability_confirmation_bars():
    engine = MarketRegimeEngine(min_confirmation_bars=2)
    candles = generate_trend_candles(70)
    snapshots = feature_service.generate_feature_series(candles, timeframe="1m")
    regimes = engine.classify_regime_series(snapshots)
    
    assert len(regimes) == 70
    # Later snapshots in steady trend must stabilize to TRENDING_UP
    assert regimes[-1].directional_regime == DirectionalRegime.TRENDING_UP

def test_future_candle_modification_regime_leakage_protection():
    """
    CRITICAL LOOK-AHEAD REGIME PROTECTION TEST:
    Modifying a future candle (index 65) MUST NOT alter the historical regime classification at index 30!
    """
    engine = MarketRegimeEngine(min_confirmation_bars=1)
    candles_original = generate_trend_candles(70)
    snaps_orig = feature_service.generate_feature_series(candles_original, timeframe="1m")
    regimes_orig = engine.classify_regime_series(snaps_orig)
    regime_at_30_orig = regimes_orig[30].directional_regime
    
    # Create modified series where index 65 is radically altered
    candles_modified = generate_trend_candles(70)
    future_c = candles_modified[65]
    candles_modified[65] = OHLCVCandle(
        symbol="NIFTY",
        timestamp=future_c.timestamp,
        interval="1m",
        open=10000.0, # Radical drop
        high=10000.0,
        low=10000.0,
        close=10000.0,
        volume=999999
    )
    
    snaps_mod = feature_service.generate_feature_series(candles_modified, timeframe="1m")
    regimes_mod = engine.classify_regime_series(snaps_mod)
    regime_at_30_mod = regimes_mod[30].directional_regime
    
    assert regime_at_30_orig == regime_at_30_mod, "Look-ahead regime leakage detected!"
