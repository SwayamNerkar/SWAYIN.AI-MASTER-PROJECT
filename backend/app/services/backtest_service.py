import logging
import datetime
from typing import Dict, Any, List, Optional

from app.schemas.backtest import (
    BacktestConfig, BacktestResult, BacktestListResponse, BacktestSummaryItem
)
from app.services.market_data_service import market_data_service
from app.engines.backtest_engine import backtest_engine, WalkForwardBacktestEngine

logger = logging.getLogger("swayin")

class BacktestService:
    """
    Coordinator Service for Backtesting Subsystem.
    Manages historical data loading, backtest execution, and result store.
    """

    def __init__(self, engine: Optional[WalkForwardBacktestEngine] = None):
        self.engine = engine or backtest_engine
        self._backtest_store: Dict[str, BacktestResult] = {}

    async def run_backtest(self, config: BacktestConfig) -> BacktestResult:
        """
        Fetches historical candles and executes walk-forward prediction evaluation.
        """
        candles = await market_data_service.get_ohlcv(config.symbol, timeframe=config.timeframe, limit=250)
        result = self.engine.run_backtest_on_candles(candles, config)
        self._backtest_store[result.backtest_id] = result
        logger.info(f"BACKTEST COMPLETE [{config.symbol} {config.timeframe}]: ID={result.backtest_id}, Predictions={result.prediction_count}, MAE={result.overall_metrics['mae']}, Improves Naive={result.improves_naive}")
        return result

    def get_backtest(self, backtest_id: str) -> Optional[BacktestResult]:
        return self._backtest_store.get(backtest_id)

    def list_backtests(self) -> BacktestListResponse:
        items = []
        for b_id, res in self._backtest_store.items():
            items.append(BacktestSummaryItem(
                backtest_id=b_id,
                symbol=res.config.symbol,
                timeframe=res.config.timeframe,
                model_version=res.config.model_version,
                created_at=res.created_at,
                prediction_count=res.prediction_count,
                mae=res.overall_metrics.get("mae", 0.0),
                rmse=res.overall_metrics.get("rmse", 0.0),
                directional_accuracy=res.overall_metrics.get("directional_accuracy", 0.0),
                improves_naive=res.improves_naive,
                status=res.status
            ))
        return BacktestListResponse(total=len(items), items=items)

    def get_backtest_predictions(self, backtest_id: str, offset: int = 0, limit: int = 50) -> Dict[str, Any]:
        res = self._backtest_store.get(backtest_id)
        if not res:
            return {"total": 0, "predictions": []}
        
        preds = res.predictions[offset:offset+limit]
        return {
            "backtest_id": backtest_id,
            "offset": offset,
            "limit": limit,
            "total": len(res.predictions),
            "predictions": preds
        }

backtest_service = BacktestService()
