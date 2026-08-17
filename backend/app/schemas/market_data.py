import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator

class IndexQuote(BaseModel):
    """
    Strongly-typed internal domain model for Index Quotes (NIFTY / SENSEX).
    """
    symbol: str = Field(description="Normalized index symbol: 'NIFTY' or 'SENSEX'")
    timestamp: datetime.datetime = Field(description="Timezone-aware timestamp (Asia/Kolkata)")
    ltp: float = Field(ge=0.0, description="Last Traded Price")
    open: float = Field(ge=0.0, description="Open price")
    high: float = Field(ge=0.0, description="High price")
    low: float = Field(ge=0.0, description="Low price")
    close: float = Field(ge=0.0, description="Close price / Previous Close")
    previous_close: Optional[float] = Field(default=None, ge=0.0, description="Previous session close")
    change: Optional[float] = Field(default=None, description="Net price change")
    change_percent: Optional[float] = Field(default=None, description="Percentage price change")
    volume: Optional[int] = Field(default=0, ge=0, description="Total traded volume")
    data_mode: str = Field(default="MOCK / SIMULATED DATA", description="Data mode label")
    provider: str = Field(default="mock", description="Market data provider name")
    timezone: str = Field(default="Asia/Kolkata", description="Timezone name")
    data_age_seconds: Optional[float] = Field(default=None, ge=0.0, description="Age of data in seconds")
    is_fresh: Optional[bool] = Field(default=None, description="Data freshness flag")

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        sym = v.upper().strip()
        if sym in ("NIFTY", "NIFTY 50", "NIFTY50", "^NSEI"):
            return "NIFTY"
        if sym in ("SENSEX", "BSESN", "^BSESN"):
            return "SENSEX"
        if sym in ("INDIAVIX", "INDIA VIX", "VIX"):
            return "INDIAVIX"
        return sym

class OHLCVCandle(BaseModel):
    """
    Strongly-typed internal domain model for OHLCV Candles.
    """
    symbol: str = Field(description="Normalized symbol")
    timestamp: datetime.datetime = Field(description="Timezone-aware timestamp (Asia/Kolkata)")
    interval: str = Field(default="1m", description="Bar interval: '1m', '5m', '15m', '1d'")
    open: float = Field(gt=0.0, description="Opening price")
    high: float = Field(gt=0.0, description="High price")
    low: float = Field(gt=0.0, description="Low price")
    close: float = Field(gt=0.0, description="Closing price")
    volume: int = Field(ge=0, description="Volume traded")
    data_mode: str = Field(default="MOCK / SIMULATED DATA", description="Data mode label")
    provider: str = Field(default="mock", description="Market data provider name")

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        valid_intervals = {"1m", "5m", "15m", "30m", "1h", "1d"}
        if v.lower() not in valid_intervals:
            raise ValueError(f"Invalid candle interval '{v}'. Must be one of {valid_intervals}")
        return v.lower()

class DataHealthStatus(BaseModel):
    """
    Exposes data age, freshness, and quality health metrics.
    """
    nifty_fresh: bool = Field(description="True if NIFTY quote age <= freshness threshold")
    sensex_fresh: bool = Field(description="True if SENSEX quote age <= freshness threshold")
    nifty_age_seconds: float = Field(ge=0.0, description="NIFTY data age in seconds")
    sensex_age_seconds: float = Field(ge=0.0, description="SENSEX data age in seconds")
    freshness_threshold_seconds: float = Field(default=10.0, description="Configured max freshness age")
    validation_passed: bool = Field(default=True, description="True if data validation checks passed")
    stale_warning: bool = Field(default=False, description="True if any active data is stale")
    provider_healthy: bool = Field(default=True, description="True if data provider is responding")

class MarketSnapshot(BaseModel):
    """
    Normalized composite Market Snapshot model.
    """
    timestamp: datetime.datetime = Field(description="Snapshot generation timestamp (Asia/Kolkata)")
    session_state: str = Field(description="Current Market Session Engine State")
    nifty: IndexQuote = Field(description="NIFTY 50 Quote")
    sensex: IndexQuote = Field(description="SENSEX Quote")
    data_health: DataHealthStatus = Field(description="Data health & freshness metrics")
    provider_status: Dict[str, Any] = Field(default_factory=dict, description="Provider status & metadata")

class OptionContractQuote(BaseModel):
    symbol: str
    option_type: str = Field(pattern="^(CE|PE)$")
    strike_price: float = Field(gt=0.0)
    ltp: float = Field(ge=0.0)
    bid: float = Field(ge=0.0)
    ask: float = Field(ge=0.0)
    iv: float = Field(ge=0.0)
    delta: float
    volume: int = Field(ge=0)
    oi: int = Field(ge=0)
    change_in_oi: int

class ValidatedOptionChain(BaseModel):
    underlying: str
    spot_price: float = Field(gt=0.0)
    atm_strike: float = Field(gt=0.0)
    expiry_date: str
    lot_size: int = Field(gt=0)
    pcr_oi: float = Field(ge=0.0)
    total_ce_oi: int = Field(ge=0)
    total_pe_oi: int = Field(ge=0)
    chain: List[Dict[str, Any]]
    timestamp: datetime.datetime
    data_mode: str = Field(default="MOCK / SIMULATED DATA")
    provider: str = Field(default="mock")
    is_validated: bool = Field(default=True)
