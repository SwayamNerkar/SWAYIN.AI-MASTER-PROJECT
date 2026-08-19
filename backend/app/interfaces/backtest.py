from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.backtest import BacktestConfig, BacktestResult

class BacktestEngineInterface(ABC):
    """
    Abstract Interface for Walk-Forward Prediction Evaluation Engines.
    Guarantees strict zero look-ahead bias and reproducible evaluation metrics.
    """

    @abstractmethod
    def run_backtest_on_candles(self, candles: list, config: BacktestConfig) -> BacktestResult:
        """Executes walk-forward backtest evaluation on given historical candle list."""
        pass
