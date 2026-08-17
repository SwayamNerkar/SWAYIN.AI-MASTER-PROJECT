import datetime
import pytest
import pytz
from app.services.market_data_service import market_data_service

IST = pytz.timezone("Asia/Kolkata")

def test_data_freshness_calculation():
    now = datetime.datetime.now(IST)
    # 2 seconds old timestamp
    ts_fresh = now - datetime.timedelta(seconds=2)
    age_fresh, is_fresh = market_data_service.calculate_data_freshness(ts_fresh)
    assert age_fresh >= 1.9
    assert is_fresh is True

    # 15 seconds old timestamp (exceeds default 10s threshold)
    ts_stale = now - datetime.timedelta(seconds=15)
    age_stale, is_stale_fresh = market_data_service.calculate_data_freshness(ts_stale)
    assert age_stale >= 14.9
    assert is_stale_fresh is False
