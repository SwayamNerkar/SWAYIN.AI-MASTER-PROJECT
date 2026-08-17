import datetime
import pytest
from app.core.session_engine import MarketSessionEngine, SessionState

session_engine = MarketSessionEngine()

def test_weekend_detection():
    # 2026-08-15 is Saturday, 2026-08-16 is Sunday
    saturday = datetime.datetime(2026, 8, 15, 10, 0, tzinfo=session_engine.IST)
    sunday = datetime.datetime(2026, 8, 16, 11, 0, tzinfo=session_engine.IST)
    
    sat_info = session_engine.get_session_info(override_time=saturday)
    sun_info = session_engine.get_session_info(override_time=sunday)
    
    assert sat_info["state"] == SessionState.SESSION_CLOSED.value
    assert sat_info["is_trading_day"] is False
    assert sat_info["new_trades_allowed"] is False
    
    assert sun_info["state"] == SessionState.SESSION_CLOSED.value
    assert sun_info["is_trading_day"] is False

def test_weekday_schedule():
    # 2026-08-17 is Monday
    mon = lambda h, m: datetime.datetime(2026, 8, 17, h, m, tzinfo=session_engine.IST)
    
    # 08:55 -> Closed
    t_0855 = session_engine.get_session_info(override_time=mon(8, 55))
    assert t_0855["state"] == SessionState.SESSION_CLOSED.value
    assert t_0855["new_trades_allowed"] is False

    # 09:00 -> PRE_MARKET
    t_0900 = session_engine.get_session_info(override_time=mon(9, 0))
    assert t_0900["state"] == SessionState.PRE_MARKET.value
    assert t_0900["new_trades_allowed"] is False

    # 09:16 -> WARMUP
    t_0916 = session_engine.get_session_info(override_time=mon(9, 16))
    assert t_0916["state"] == SessionState.WARMUP.value
    assert t_0916["is_market_open"] is True
    assert t_0916["new_trades_allowed"] is False

    # 09:20 -> SIGNAL_ENGINE_ACTIVE
    t_0920 = session_engine.get_session_info(override_time=mon(9, 20))
    assert t_0920["state"] == SessionState.SIGNAL_ENGINE_ACTIVE.value
    assert t_0920["new_trades_allowed"] is True
    assert t_0920["exit_monitoring_active"] is True

    # 15:15 -> NO_NEW_TRADES
    t_1515 = session_engine.get_session_info(override_time=mon(15, 15))
    assert t_1515["state"] == SessionState.NO_NEW_TRADES.value
    assert t_1515["new_trades_allowed"] is False
    assert t_1515["exit_monitoring_active"] is True

    # 15:25 -> FINAL_EXIT_WARNING
    t_1525 = session_engine.get_session_info(override_time=mon(15, 25))
    assert t_1525["state"] == SessionState.FINAL_EXIT_WARNING.value
    assert t_1525["new_trades_allowed"] is False
    assert t_1525["exit_monitoring_active"] is True

    # 15:30 -> SESSION_CLOSED
    t_1530 = session_engine.get_session_info(override_time=mon(15, 30))
    assert t_1530["state"] == SessionState.SESSION_CLOSED.value
    assert t_1530["new_trades_allowed"] is False
    assert t_1530["is_market_open"] is False
