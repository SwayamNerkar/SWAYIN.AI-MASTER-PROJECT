import pytest
from test_dataset_builder import generate_mock_candles
from app.schemas.backtest import BacktestConfig
from app.engines.backtest_engine import backtest_engine

def test_backtest_future_candle_modification_leakage_protection():
    """
    CRITICAL BACKTEST LEAKAGE PROTECTION TEST:
    Modifying a future candle (e.g. index 130) MUST NOT alter prediction records at earlier timestamp (e.g. index 80)!
    """
    config = BacktestConfig(
        symbol="NIFTY",
        timeframe="1m",
        horizon_bars=3,
        initial_train_bars=70,
        eval_window_bars=10
    )
    
    # Run backtest on original candles
    candles_orig = generate_mock_candles(150)
    res_orig = backtest_engine.run_backtest_on_candles(candles_orig, config)
    rec_at_10_orig = res_orig.predictions[5].prediction  # Prediction at earlier index
    
    # Create modified candles series where index 140 is radically altered
    candles_mod = generate_mock_candles(150)
    candles_mod[140].close = 99999.0
    candles_mod[140].high = 99999.0
    
    res_mod = backtest_engine.run_backtest_on_candles(candles_mod, config)
    rec_at_10_mod = res_mod.predictions[5].prediction
    
    assert rec_at_10_orig == pytest.approx(rec_at_10_mod), "Walk-forward future leakage detected! Modifying future candle altered past prediction!"
