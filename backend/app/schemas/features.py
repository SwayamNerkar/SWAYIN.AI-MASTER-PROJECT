import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class FeatureCategory(str, Enum):
    PRICE = "price"
    TREND = "trend"
    MOMENTUM = "momentum"
    VOLATILITY = "volatility"
    VOLUME = "volume"
    PRICE_ACTION = "price_action"
    MARKET_CONTEXT = "market_context"

class FeatureMetadata(BaseModel):
    """
    Metadata definition for ML feature engineering pipeline.
    """
    feature_name: str = Field(description="Unique feature identifier name (e.g. 'rsi_14')")
    category: FeatureCategory = Field(description="Feature domain category")
    source: str = Field(default="OHLCV", description="Source data stream")
    timeframe: str = Field(default="1m", description="Bar timeframe: '1m', '5m'")
    period: Optional[int] = Field(default=None, description="Lookback window period")
    description: str = Field(description="Description of what this feature represents")
    dtype: str = Field(default="float64", description="Data type: 'float64', 'int64'")
    nullable: bool = Field(default=True, description="True if value can be None during warmup")
    requires_volume: bool = Field(default=False, description="True if feature requires volume data")

class FeatureSnapshot(BaseModel):
    """
    Strongly typed feature snapshot for a single symbol at a given timestamp and timeframe.
    """
    timestamp: datetime.datetime = Field(description="Timezone-aware feature timestamp (Asia/Kolkata)")
    symbol: str = Field(description="Normalized symbol (NIFTY / SENSEX)")
    timeframe: str = Field(default="1m", description="Timeframe: '1m', '5m'")
    features: Dict[str, Optional[float]] = Field(description="Dictionary of calculated feature values")
    feature_validity: Dict[str, bool] = Field(description="Boolean dict indicating if warmup period is satisfied")
    is_snapshot_valid: bool = Field(default=True, description="True if required core features are valid")
    warmup_ready: bool = Field(default=True, description="True if minimum historical window is satisfied")
    data_mode: str = Field(default="MOCK / SIMULATED DATA", description="Data mode label")
    provider: str = Field(default="mock", description="Data provider source")

class FeatureSeriesResponse(BaseModel):
    symbol: str
    timeframe: str
    total_snapshots: int
    warmup_period_bars: int
    snapshots: List[FeatureSnapshot]
    metadata: List[FeatureMetadata]
