from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class IndexQuoteResponse(BaseModel):
    symbol: str
    ltp: float
    change: float
    change_percent: float
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: str
    data_mode: str
    is_simulated: bool

class OHLCVBar(BaseModel):
    timestamp: str
    symbol: str
    timeframe: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    data_mode: str

class MarketSnapshotResponse(BaseModel):
    timestamp: str
    data_mode: str
    snapshot: Dict[str, Any]
