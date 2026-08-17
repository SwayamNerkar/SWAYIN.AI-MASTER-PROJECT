import datetime
import pytest
import pytz
from app.services.validation_service import validation_service, MarketDataValidationError
from app.schemas.market_data import IndexQuote, OHLCVCandle

IST = pytz.timezone("Asia/Kolkata")

def test_valid_quote():
    now = datetime.datetime.now(IST)
    quote = IndexQuote(
        symbol="NIFTY",
        timestamp=now,
        ltp=24500.0,
        open=24480.0,
        high=24520.0,
        low=24450.0,
        close=24500.0,
        volume=150000
    )
    assert validation_service.validate_quote(quote) is True

def test_corrupted_high_low_rejection():
    now = datetime.datetime.now(IST)
    # High < Low -> invalid
    with pytest.raises(MarketDataValidationError, match="High .* < Low"):
        candle = OHLCVCandle(
            symbol="NIFTY",
            timestamp=now,
            interval="1m",
            open=24500.0,
            high=24400.0, # Corrupted
            low=24550.0,
            close=24500.0,
            volume=100
        )
        validation_service.validate_candle(candle)

def test_corrupted_high_less_than_open_rejection():
    now = datetime.datetime.now(IST)
    # High is less than open -> invalid
    with pytest.raises(MarketDataValidationError, match="less than max"):
        candle = OHLCVCandle(
            symbol="NIFTY",
            timestamp=now,
            interval="1m",
            open=24500.0,
            high=24450.0, # Less than open
            low=24400.0,
            close=24420.0,
            volume=100
        )
        validation_service.validate_candle(candle)

def test_duplicate_timestamp_series_rejection():
    now = datetime.datetime.now(IST)
    c1 = OHLCVCandle(symbol="NIFTY", timestamp=now, interval="1m", open=24500, high=24510, low=24490, close=24505, volume=10)
    c2 = OHLCVCandle(symbol="NIFTY", timestamp=now, interval="1m", open=24505, high=24515, low=24495, close=24510, volume=20) # Duplicate timestamp
    
    with pytest.raises(MarketDataValidationError, match="Duplicate timestamp"):
        validation_service.validate_candle_series([c1, c2])

def test_option_chain_validation():
    valid_chain = {
        "underlying": "NIFTY",
        "spot_price": 24500.0,
        "chain": [
            {
                "strike_price": 24500.0,
                "CE": {"symbol": "NIFTY24500CE", "ltp": 180.0, "oi": 50000, "iv": 15.0},
                "PE": {"symbol": "NIFTY24500PE", "ltp": 160.0, "oi": 60000, "iv": 14.5}
            }
        ]
    }
    assert validation_service.validate_option_chain(valid_chain) is True

    invalid_chain = {
        "underlying": "NIFTY",
        "spot_price": 24500.0,
        "chain": [
            {
                "strike_price": 24500.0,
                "CE": {"symbol": "NIFTY24500CE", "ltp": -10.0, "oi": 50000, "iv": 15.0}, # Negative LTP
                "PE": {"symbol": "NIFTY24500PE", "ltp": 160.0, "oi": 60000, "iv": 14.5}
            }
        ]
    }
    with pytest.raises(MarketDataValidationError, match="Negative LTP"):
        validation_service.validate_option_chain(invalid_chain)
