import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class WalkForwardMode(str, Enum):
    EXPANDING = "EXPANDING"
    ROLLING = "ROLLING"

class BacktestConfig(BaseModel):
    symbol: str = Field(default="NIFTY", description="Target index symbol ('NIFTY' or 'SENSEX')")
    timeframe: str = Field(default="1m", description="Bar timeframe ('1m', '5m')")
    model_version: str = Field(default="v1.0.0", description="Target model version string")
    horizon_bars: int = Field(default=3, ge=1, le=10, description="Future return target horizon in bars")
    walk_forward_mode: WalkForwardMode = Field(default=WalkForwardMode.EXPANDING, description="Walk-forward window mode ('EXPANDING' or 'ROLLING')")
    initial_train_bars: int = Field(default=100, ge=30, description="Initial historical training window size in bars")
    eval_window_bars: int = Field(default=10, ge=1, description="Size of each evaluation step window in bars")
    retrain_frequency: str = Field(default="window", description="Retraining schedule ('window', 'daily')")
    start_timestamp: Optional[datetime.datetime] = Field(default=None, description="Optional start datetime boundary")
    end_timestamp: Optional[datetime.datetime] = Field(default=None, description="Optional end datetime boundary")

class BacktestPredictionRecord(BaseModel):
    """
    Individual walk-forward prediction vs actual outcome record.
    Pure evaluation data point — NOT a trading execution signal.
    """
    timestamp: datetime.datetime = Field(description="Prediction bar timestamp (Asia/Kolkata)")
    symbol: str
    timeframe: str
    model_id: str
    model_version: str
    prediction: float = Field(description="Predicted future return value")
    actual: float = Field(description="Actual future return value")
    prediction_error: float = Field(description="Actual return - predicted return")
    absolute_error: float = Field(description="Abs(Actual return - predicted return)")
    squared_error: float = Field(description="(Actual return - predicted return)^2")
    predicted_direction: str = Field(description="Predicted direction: 'UP', 'DOWN', 'FLAT'")
    actual_direction: str = Field(description="Actual direction: 'UP', 'DOWN', 'FLAT'")
    direction_correct: bool = Field(description="True if predicted sign matches actual sign")
    horizon_bars: int
    directional_regime: Optional[str] = Field(default=None, description="Historical market regime (Task 1.4)")
    volatility_state: Optional[str] = Field(default=None, description="Historical volatility state (Task 1.4)")
    regime_confidence: Optional[float] = Field(default=None, description="Historical regime confidence")
    data_mode: str = Field(default="MOCK / SIMULATED DATA")
    provider: str = Field(default="mock")

class GroupedMetrics(BaseModel):
    sample_count: int
    mae: float
    rmse: float
    directional_accuracy: float
    mean_error: float

class ErrorAnalysisSummary(BaseModel):
    mean_prediction: float
    mean_actual: float
    prediction_bias: float = Field(description="Mean prediction - mean actual")
    median_abs_error: float
    max_abs_error: float
    consecutive_errors_max: int = Field(default=0)

class BacktestResult(BaseModel):
    """
    Complete walk-forward prediction evaluation report.
    """
    backtest_id: str
    config: BacktestConfig
    created_at: datetime.datetime
    total_candles: int
    prediction_count: int
    skipped_count: int
    warmup_rows_skipped: int
    overall_metrics: Dict[str, float] = Field(description="Overall MAE, RMSE, R2, Directional Accuracy")
    naive_metrics: Dict[str, float] = Field(description="Naive zero-return baseline metrics")
    improves_naive: bool = Field(description="True if model RMSE beats naive zero-return baseline RMSE")
    regime_metrics: Dict[str, GroupedMetrics] = Field(description="Subgroup performance metrics broken down by Task 1.4 Regime")
    volatility_metrics: Dict[str, GroupedMetrics] = Field(description="Subgroup performance metrics broken down by Task 1.4 Volatility State")
    error_analysis: ErrorAnalysisSummary
    predictions: List[BacktestPredictionRecord]
    data_mode: str = Field(default="MOCK / SIMULATED DATA")
    provider: str = Field(default="mock")
    status: str = Field(default="COMPLETED")

class BacktestSummaryItem(BaseModel):
    backtest_id: str
    symbol: str
    timeframe: str
    model_version: str
    created_at: datetime.datetime
    prediction_count: int
    mae: float
    rmse: float
    directional_accuracy: float
    improves_naive: bool
    status: str

class BacktestListResponse(BaseModel):
    total: int
    items: List[BacktestSummaryItem]
