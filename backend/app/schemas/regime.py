import datetime
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DirectionalRegime(str, Enum):
    TRENDING_UP = "TRENDING_UP"
    TRENDING_DOWN = "TRENDING_DOWN"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    REVERSAL = "REVERSAL"

class VolatilityState(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class MarketRegimeSnapshot(BaseModel):
    """
    Strongly typed market regime classification snapshot.
    Descriptive context for ML, strategy, and risk engines.
    """
    symbol: str = Field(description="Normalized symbol: 'NIFTY' or 'SENSEX'")
    timestamp: datetime.datetime = Field(description="Classification timestamp (Asia/Kolkata)")
    timeframe: str = Field(default="1m", description="Bar timeframe: '1m', '5m'")
    directional_regime: DirectionalRegime = Field(description="Primary directional regime state")
    volatility_state: VolatilityState = Field(description="Volatility state machine state")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence score (0.0 to 1.0)")
    reasons: List[str] = Field(description="Machine-readable evidence reason codes")
    feature_timestamp: datetime.datetime = Field(description="Timestamp of source feature snapshot")
    session_state: str = Field(description="Current market session state")
    validity_status: str = Field(default="VALID", description="Regime status: 'VALID', 'WARMUP', 'UNAVAILABLE', 'SESSION_CLOSED'")
    data_mode: str = Field(default="MOCK / SIMULATED DATA", description="Data mode label")
    provider: str = Field(default="mock", description="Market data provider name")

class VolatilityTransitionLog(BaseModel):
    """
    Log of state transitions in the Volatility State Machine.
    """
    symbol: str
    timestamp: datetime.datetime
    previous_state: VolatilityState
    current_state: VolatilityState
    measured_volatility: float = Field(description="Measured normalized ATR / realized vol")
    threshold_used: float = Field(description="Threshold boundary that triggered transition")
    reason: str = Field(description="Explanation of state change")

class RegimeHistoryResponse(BaseModel):
    symbol: str
    timeframe: str
    total_snapshots: int
    snapshots: List[MarketRegimeSnapshot]
    transitions: List[VolatilityTransitionLog]
