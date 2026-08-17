import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PredictionTarget(str, Enum):
    FUTURE_RETURN = "future_return"
    FUTURE_DIRECTION = "future_direction"

class ModelStatus(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    VALIDATED = "VALIDATED"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"

class ModelMetrics(BaseModel):
    mae: float = Field(description="Mean Absolute Error")
    rmse: float = Field(description="Root Mean Squared Error")
    r2: float = Field(description="R-squared coefficient of determination")
    directional_accuracy: float = Field(ge=0.0, le=1.0, description="Percentage of correct directional predictions")
    naive_mae: float = Field(description="MAE of naive zero-return baseline")
    naive_rmse: float = Field(description="RMSE of naive zero-return baseline")
    improves_naive: bool = Field(description="True if model outperforms naive zero-return baseline on RMSE")

class ModelMetadata(BaseModel):
    model_id: str = Field(description="Unique UUID string for model instance")
    model_name: str = Field(default="GradientBoostingRegressor")
    model_version: str = Field(description="Version string e.g. v1.0.0")
    training_timestamp: datetime.datetime
    symbol: str
    timeframe: str
    target: PredictionTarget
    target_horizon: int = Field(description="Future horizon in bars e.g. 3")
    feature_list: List[str] = Field(description="Deterministic feature column list")
    training_rows: int
    validation_rows: int
    test_rows: int
    metrics: ModelMetrics
    status: ModelStatus = Field(default=ModelStatus.EXPERIMENTAL)
    data_mode: str = Field(default="MOCK / SIMULATED DATA")
    preprocessing_version: str = Field(default="v1")

class PredictionResponse(BaseModel):
    """
    Typed prediction output DTO.
    Pure predictive value — NOT a trading signal or order recommendation.
    """
    symbol: str
    timestamp: datetime.datetime
    timeframe: str
    model_id: str
    model_version: str
    prediction_target: str
    horizon_bars: int
    predicted_value: float = Field(description="Predicted numerical value e.g. predicted future return")
    predicted_direction: Optional[str] = Field(default=None, description="Derived direction: 'UP', 'DOWN', 'FLAT'")
    data_mode: str = Field(default="MOCK / SIMULATED DATA")
    model_status: ModelStatus = Field(default=ModelStatus.EXPERIMENTAL)
