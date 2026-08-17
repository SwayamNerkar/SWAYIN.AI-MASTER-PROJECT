from pydantic import BaseModel
from typing import Optional

class CalculateCostRequest(BaseModel):
    symbol: str = "NIFTY24500CE"
    entry_price: float = 180.0
    exit_price: float = 220.0
    quantity: int = 25
    custom_slippage_pts: Optional[float] = None
