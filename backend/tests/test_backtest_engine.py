import pytest
from test_dataset_builder import generate_mock_candles
from app.schemas.backtest import BacktestConfig
from app.engines.backtest_engine import backtest_engine

def test_walk_forward_backtest_execution():
    candles = generate_mock_candles(150)
    config = BacktestConfig(
        symbol="NIFTY",
        timeframe="1m",
        model_version="v1.0.0",
        horizon_bars=3,
        initial_train_bars=70,
        eval_window_bars=10
    )
    
    result = backtest_engine.run_backtest_on_candles(candles, config)
    
    assert result.status == "COMPLETED"
    assert result.prediction_count > 0
    assert "mae" in result.overall_metrics
    assert "rmse" in result.overall_metrics
    assert "directional_accuracy" in result.overall_metrics
    assert "mae" in result.naive_metrics
    
    # Verify strict temporal ordering of prediction records
    preds = result.predictions
    for i in range(len(preds) - 1):
        assert preds[i].timestamp <= preds[i+1].timestamp, "Prediction timestamps out of chronological order!"

def test_backtest_engine_insufficient_data_rejection():
    candles = generate_mock_candles(40)
    config = BacktestConfig(initial_train_bars=70, eval_window_bars=10)
    with pytest.raises(ValueError):
        backtest_engine.run_backtest_on_candles(candles, config)
