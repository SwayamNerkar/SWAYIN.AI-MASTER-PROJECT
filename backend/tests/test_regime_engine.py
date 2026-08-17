import datetime
import pytest
import pytz
from app.schemas.features import FeatureSnapshot
from app.schemas.regime import DirectionalRegime, VolatilityState
from app.engines.regime_engine import MarketRegimeEngine

IST = pytz.timezone("Asia/Kolkata")

def make_feature_snap(feats: dict) -> FeatureSnapshot:
    now = datetime.datetime.now(IST)
    return FeatureSnapshot(
        timestamp=now,
        symbol="NIFTY",
        timeframe="1m",
        features=feats,
        feature_validity={k: True for k in feats.keys()},
        is_snapshot_valid=True,
        warmup_ready=True
    )

def test_trending_up_classification():
    engine = MarketRegimeEngine(min_confirmation_bars=1)
    bullish_feats = {
        "ema_9": 24520.0,
        "ema_21": 24500.0,
        "ema_50": 24450.0,
        "plus_di": 30.0,
        "minus_di": 12.0,
        "adx": 28.0,
        "rsi_14": 62.0,
        "macd_hist": 5.2,
        "normalized_atr": 1.4
    }
    snap = make_feature_snap(bullish_feats)
    regime_snap = engine.classify_regime(snap)
    
    assert regime_snap.directional_regime == DirectionalRegime.TRENDING_UP
    assert regime_snap.confidence >= 0.60
    assert "EMA_9_ABOVE_EMA_21" in regime_snap.reasons
    assert "ADX_TREND_STRONG" in regime_snap.reasons

def test_trending_down_classification():
    engine = MarketRegimeEngine(min_confirmation_bars=1)
    bearish_feats = {
        "ema_9": 24420.0,
        "ema_21": 24450.0,
        "ema_50": 24500.0,
        "plus_di": 10.0,
        "minus_di": 32.0,
        "adx": 30.0,
        "rsi_14": 38.0,
        "macd_hist": -6.5,
        "normalized_atr": 1.5
    }
    snap = make_feature_snap(bearish_feats)
    regime_snap = engine.classify_regime(snap)
    
    assert regime_snap.directional_regime == DirectionalRegime.TRENDING_DOWN
    assert regime_snap.confidence >= 0.60
    assert "EMA_9_BELOW_EMA_21" in regime_snap.reasons

def test_sideways_classification():
    engine = MarketRegimeEngine(min_confirmation_bars=1)
    sideways_feats = {
        "ema_9": 24500.0,
        "ema_21": 24501.0,
        "ema_50": 24499.0,
        "plus_di": 15.0,
        "minus_di": 16.0,
        "adx": 12.0,  # Below ADX threshold (20)
        "rsi_14": 50.5,
        "macd_hist": 0.1,
        "normalized_atr": 0.8
    }
    snap = make_feature_snap(sideways_feats)
    regime_snap = engine.classify_regime(snap)
    
    assert regime_snap.directional_regime == DirectionalRegime.SIDEWAYS
    assert "SIDEWAYS_CONSOLIDATION" in regime_snap.reasons
