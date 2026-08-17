import datetime
import pytest
import numpy as np
import pandas as pd
from app.engines.indicator_engine import TechnicalIndicatorEngine

@pytest.fixture
def sample_ohlcv_df():
    """Generates 50 deterministic synthetic candles for indicator testing."""
    dates = pd.date_range(start="2026-08-17 09:15", periods=50, freq="1min")
    np.random.seed(42)
    close_prices = 24500.0 + np.cumsum(np.random.randn(50) * 5.0)
    
    rows = []
    for i in range(50):
        c = close_prices[i]
        o = c - np.random.uniform(-2, 2)
        h = max(o, c) + np.random.uniform(0, 3)
        l = min(o, c) - np.random.uniform(0, 3)
        v = int(np.random.uniform(10000, 50000))
        rows.append({
            "timestamp": dates[i],
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "volume": v
        })
    return pd.DataFrame(rows)

def test_price_features(sample_ohlcv_df):
    engine = TechnicalIndicatorEngine()
    df_feat = engine.calculate_all_features(sample_ohlcv_df)
    
    assert "price_change_pct" in df_feat.columns
    assert "candle_body" in df_feat.columns
    assert "upper_wick" in df_feat.columns
    assert "lower_wick" in df_feat.columns
    assert "candle_range" in df_feat.columns
    
    # Check non-negative wick and range
    assert (df_feat["candle_range"] >= 0).all()
    assert (df_feat["upper_wick"] >= 0).all()
    assert (df_feat["lower_wick"] >= 0).all()

def test_trend_indicators(sample_ohlcv_df):
    engine = TechnicalIndicatorEngine()
    df_feat = engine.calculate_all_features(sample_ohlcv_df)
    
    assert "sma_10" in df_feat.columns
    assert "ema_9" in df_feat.columns
    assert "vwap" in df_feat.columns
    assert "macd_line" in df_feat.columns
    assert "macd_signal" in df_feat.columns
    assert "adx" in df_feat.columns
    
    # Check VWAP positivity
    valid_vwap = df_feat["vwap"].dropna()
    assert len(valid_vwap) > 0
    assert (valid_vwap > 20000).all()

def test_momentum_and_volatility_indicators(sample_ohlcv_df):
    engine = TechnicalIndicatorEngine()
    df_feat = engine.calculate_all_features(sample_ohlcv_df)
    
    assert "rsi_14" in df_feat.columns
    assert "stoch_k" in df_feat.columns
    assert "atr_14" in df_feat.columns
    assert "normalized_atr" in df_feat.columns
    
    # RSI bounded 0..100
    valid_rsi = df_feat["rsi_14"].dropna()
    assert (valid_rsi >= 0.0).all() and (valid_rsi <= 100.0).all()
