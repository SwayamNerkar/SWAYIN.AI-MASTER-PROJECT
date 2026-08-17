import datetime
import pytest
import numpy as np
import pandas as pd
import pytz

from app.schemas.market_data import OHLCVCandle
from app.services.feature_service import FeatureEngineeringService, feature_service

IST = pytz.timezone("Asia/Kolkata")

def generate_mock_candles(count: int = 40) -> list[OHLCVCandle]:
    base_time = datetime.datetime(2026, 8, 17, 9, 15, tzinfo=IST)
    candles = []
    np.random.seed(123)
    c = 24500.0
    for i in range(count):
        t = base_time + datetime.timedelta(minutes=i)
        c += np.random.uniform(-5, 5)
        o = c - np.random.uniform(-2, 2)
        h = max(o, c) + np.random.uniform(0, 3)
        l = min(o, c) - np.random.uniform(0, 3)
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

def test_future_candle_modification_leakage_protection():
    """
    CRITICAL LOOK-AHEAD PROTECTION TEST:
    Modifying a future candle (e.g. index 35) MUST NOT alter any feature values at index 20!
    """
    candles_original = generate_mock_candles(40)
    
    # Calculate features on original series
    snapshots_orig = feature_service.generate_feature_series(candles_original, timeframe="1m")
    feat_at_20_orig = snapshots_orig[20].features.copy()
    
    # Create modified series where future candle (index 35) is radically altered
    candles_modified = generate_mock_candles(40)
    future_c = candles_modified[35]
    candles_modified[35] = OHLCVCandle(
        symbol="NIFTY",
        timestamp=future_c.timestamp,
        interval="1m",
        open=99999.0, # Radical future spike
        high=99999.0,
        low=99999.0,
        close=99999.0,
        volume=9999999
    )
    
    # Calculate features on modified series
    snapshots_mod = feature_service.generate_feature_series(candles_modified, timeframe="1m")
    feat_at_20_mod = snapshots_mod[20].features.copy()
    
    # Verify index 20 features are 100% IDENTICAL
    for k in feat_at_20_orig.keys():
        assert feat_at_20_orig[k] == feat_at_20_mod[k], f"Look-ahead leakage detected in feature '{k}' at index 20!"

def test_appending_future_candles_leakage_protection():
    """
    Appending additional future candles (increasing dataset length from 30 to 45)
    MUST NOT alter the feature snapshot generated for index 25!
    """
    candles_short = generate_mock_candles(30)
    candles_long = generate_mock_candles(45) # Same prefix 0..29, but with 15 extra future bars
    
    snap_short_25 = feature_service.generate_feature_series(candles_short)[25].features
    snap_long_25 = feature_service.generate_feature_series(candles_long)[25].features
    
    for k in snap_short_25.keys():
        assert snap_short_25[k] == snap_long_25[k], f"Look-ahead leakage detected when appending future bars for feature '{k}'"
