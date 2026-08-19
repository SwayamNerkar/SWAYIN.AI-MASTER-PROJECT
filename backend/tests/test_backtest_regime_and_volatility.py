import pytest
from test_dataset_builder import generate_mock_candles
from app.schemas.backtest import BacktestConfig
from app.engines.backtest_engine import backtest_engine

def test_backtest_regime_and_volatility_groupings():
    candles = generate_mock_candles(150)
    config = BacktestConfig(
        symbol="NIFTY",
        timeframe="1m",
        initial_train_bars=70,
        eval_window_bars=10
    )
    
    result = backtest_engine.run_backtest_on_candles(candles, config)
    
    # 1. Regime subgroup metrics
    assert "TRENDING_UP" in result.regime_metrics
    assert "SIDEWAYS" in result.regime_metrics
    assert isinstance(result.regime_metrics["SIDEWAYS"].sample_count, int)
    
    # 2. Volatility subgroup metrics
    assert "LOW" in result.volatility_metrics
    assert "MEDIUM" in result.volatility_metrics
    assert isinstance(result.volatility_metrics["MEDIUM"].sample_count, int)
    
    # 3. Error analysis summary
    assert result.error_analysis is not None
    assert isinstance(result.error_analysis.prediction_bias, float)
