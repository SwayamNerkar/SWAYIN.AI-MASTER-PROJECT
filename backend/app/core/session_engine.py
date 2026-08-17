import datetime
from enum import Enum
from typing import Optional, Dict, Any
import pytz

class SessionState(str, Enum):
    PRE_MARKET = "PRE_MARKET"
    MARKET_OPEN = "MARKET_OPEN"
    WARMUP = "WARMUP"
    SIGNAL_ENGINE_ACTIVE = "SIGNAL_ENGINE_ACTIVE"
    NO_NEW_TRADES = "NO_NEW_TRADES"
    EXIT_MONITORING = "EXIT_MONITORING"
    FINAL_EXIT_WARNING = "FINAL_EXIT_WARNING"
    SESSION_CLOSED = "SESSION_CLOSED"

class MarketSessionEngine:
    """
    State machine for Indian Index Options Trading Session (NSE/BSE).
    Operating in Asia/Kolkata timezone.
    
    Timeline:
    09:00 - 09:15: PRE_MARKET (Pre-market analysis)
    09:15 - 09:20: MARKET_OPEN / WARMUP (Warm-up observation)
    09:20 - 15:15: SIGNAL_ENGINE_ACTIVE (Active signal generation)
    15:15 - 15:25: NO_NEW_TRADES / EXIT_MONITORING (No new positions)
    15:25 - 15:30: FINAL_EXIT_WARNING (Strong close warning)
    15:30+: SESSION_CLOSED (Market closed)
    Saturday / Sunday: SESSION_CLOSED
    """
    
    IST = pytz.timezone("Asia/Kolkata")
    
    def __init__(self, holiday_calendar: Optional[list] = None):
        # Hook for future exchange holiday list (YYYY-MM-DD strings)
        self.holiday_calendar = holiday_calendar or []
        
    def get_current_ist_time(self, override_time: Optional[datetime.datetime] = None) -> datetime.datetime:
        """Returns localized IST datetime. Accepts optional override for testing/simulation."""
        if override_time:
            if override_time.tzinfo is None:
                return self.IST.localize(override_time)
            return override_time.astimezone(self.IST)
        return datetime.datetime.now(self.IST)

    def is_trading_day(self, dt: datetime.datetime) -> bool:
        """Checks if given date is a weekday and not an exchange holiday."""
        # 0 = Monday, ..., 5 = Saturday, 6 = Sunday
        if dt.weekday() in (5, 6):
            return False
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in self.holiday_calendar:
            return False
        return True

    def get_session_info(self, override_time: Optional[datetime.datetime] = None) -> Dict[str, Any]:
        """Calculates current market session state and operational flags."""
        now = self.get_current_ist_time(override_time)
        trading_day = self.is_trading_day(now)
        
        # Default flags for closed market
        if not trading_day:
            return {
                "state": SessionState.SESSION_CLOSED.value,
                "current_date": now.strftime("%Y-%m-%d"),
                "current_time_ist": now.strftime("%H:%M:%S"),
                "day_of_week": now.strftime("%A"),
                "is_trading_day": False,
                "is_market_open": False,
                "new_trades_allowed": False,
                "exit_monitoring_active": False,
                "next_transition": "Next trading day at 09:00:00 IST",
                "message": "Market is closed for weekend or holiday."
            }
            
        time_sec = now.hour * 3600 + now.minute * 60 + now.second
        
        # Seconds since midnight IST:
        # 09:00 = 32400
        # 09:15 = 33300
        # 09:20 = 33600
        # 15:15 = 54900
        # 15:25 = 55500
        # 15:30 = 55800

        t_0900 = 9 * 3600
        t_0915 = 9 * 3600 + 15 * 60
        t_0920 = 9 * 3600 + 20 * 60
        t_1515 = 15 * 3600 + 15 * 60
        t_1525 = 15 * 3600 + 25 * 60
        t_1530 = 15 * 3600 + 30 * 60

        state = SessionState.SESSION_CLOSED
        new_trades_allowed = False
        exit_monitoring_active = False
        is_market_open = False
        next_transition = ""
        message = ""

        if time_sec < t_0900:
            state = SessionState.SESSION_CLOSED
            next_transition = "09:00:00 IST (Pre-Market Analysis)"
            message = "Pre-market period has not started."

        elif t_0900 <= time_sec < t_0915:
            state = SessionState.PRE_MARKET
            next_transition = "09:15:00 IST (Market Open / Warmup)"
            message = "Pre-market analysis active. Analyzing overnight/global context."

        elif t_0915 <= time_sec < t_0920:
            # 09:15 exact is MARKET_OPEN, 09:15-09:20 is WARMUP
            state = SessionState.WARMUP
            is_market_open = True
            next_transition = "09:20:00 IST (Signal Engine Active)"
            message = "Market open. Warming up features and observing volatility."

        elif t_0920 <= time_sec < t_1515:
            state = SessionState.SIGNAL_ENGINE_ACTIVE
            is_market_open = True
            new_trades_allowed = True
            exit_monitoring_active = True
            next_transition = "15:15:00 IST (No New Trades Cutoff)"
            message = "Trading signal engine active. Intraday trade signals enabled."

        elif t_1515 <= time_sec < t_1525:
            state = SessionState.NO_NEW_TRADES
            is_market_open = True
            new_trades_allowed = False
            exit_monitoring_active = True
            next_transition = "15:25:00 IST (Final Exit Warning)"
            message = "Cutoff reached. No new trades allowed. Position exit monitoring active."

        elif t_1525 <= time_sec < t_1530:
            state = SessionState.FINAL_EXIT_WARNING
            is_market_open = True
            new_trades_allowed = False
            exit_monitoring_active = True
            next_transition = "15:30:00 IST (Session Closed)"
            message = "FINAL WARNING: All intraday option positions must be closed before 15:30."

        else:  # time_sec >= t_1530
            state = SessionState.SESSION_CLOSED
            is_market_open = False
            new_trades_allowed = False
            exit_monitoring_active = False
            next_transition = "Tomorrow 09:00:00 IST (Pre-Market)"
            message = "Intraday session closed. Post-market journal & analytics active."

        return {
            "state": state.value,
            "current_date": now.strftime("%Y-%m-%d"),
            "current_time_ist": now.strftime("%H:%M:%S"),
            "day_of_week": now.strftime("%A"),
            "is_trading_day": True,
            "is_market_open": is_market_open,
            "new_trades_allowed": new_trades_allowed,
            "exit_monitoring_active": exit_monitoring_active,
            "next_transition": next_transition,
            "message": message
        }

session_engine = MarketSessionEngine()
