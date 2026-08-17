from pydantic import BaseModel

class SessionStateResponse(BaseModel):
    state: str
    current_date: str
    current_time_ist: str
    day_of_week: str
    is_trading_day: bool
    is_market_open: bool
    new_trades_allowed: bool
    exit_monitoring_active: bool
    next_transition: str
    message: str
