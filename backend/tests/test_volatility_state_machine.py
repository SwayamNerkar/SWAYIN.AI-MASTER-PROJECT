import datetime
import pytest
import pytz
from app.schemas.features import FeatureSnapshot
from app.schemas.regime import VolatilityState
from app.engines.volatility_state_machine import VolatilityStateMachine

IST = pytz.timezone("Asia/Kolkata")

def make_snap(norm_atr: float) -> FeatureSnapshot:
    now = datetime.datetime.now(IST)
    return FeatureSnapshot(
        timestamp=now,
        symbol="NIFTY",
        timeframe="1m",
        features={"normalized_atr": norm_atr},
        feature_validity={"normalized_atr": True},
        is_snapshot_valid=True,
        warmup_ready=True
    )

def test_volatility_state_evaluations():
    machine = VolatilityStateMachine(low_threshold=1.0, high_threshold=2.5, hysteresis_factor=0.15)
    
    # 1. Medium initial state
    s1, t1 = machine.evaluate_state(make_snap(1.5))
    assert s1 == VolatilityState.MEDIUM

    # 2. Drop below low threshold -> LOW
    s2, t2 = machine.evaluate_state(make_snap(0.8))
    assert s2 == VolatilityState.LOW
    assert t2 is not None
    assert t2.previous_state == VolatilityState.MEDIUM
    assert t2.current_state == VolatilityState.LOW

    # 3. Spike above high threshold + hysteresis (2.5 * 1.15 = 2.875) -> HIGH
    s3, t3 = machine.evaluate_state(make_snap(3.0))
    assert s3 == VolatilityState.HIGH
    assert t3 is not None
    assert t3.current_state == VolatilityState.HIGH

def test_volatility_hysteresis_buffer():
    machine = VolatilityStateMachine(low_threshold=1.0, high_threshold=2.5, hysteresis_factor=0.15)
    
    # Force state to LOW
    machine.evaluate_state(make_snap(0.7))
    
    # Minor rise to 1.05 (above 1.0, but below hysteresis trigger 1.15) -> Should stay LOW
    s_minor, t_minor = machine.evaluate_state(make_snap(1.05))
    assert s_minor == VolatilityState.LOW
    assert t_minor is None  # No noisy transition trigger
