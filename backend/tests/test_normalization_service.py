import datetime
import pytest
from app.services.normalization_service import normalization_service

def test_symbol_normalization():
    assert normalization_service.normalize_symbol("nifty") == "NIFTY"
    assert normalization_service.normalize_symbol("NIFTY 50") == "NIFTY"
    assert normalization_service.normalize_symbol("^NSEI") == "NIFTY"
    assert normalization_service.normalize_symbol("sensex") == "SENSEX"
    assert normalization_service.normalize_symbol("^BSESN") == "SENSEX"
    assert normalization_service.normalize_symbol("vix") == "INDIAVIX"

def test_timestamp_normalization():
    # Naive timestamp -> localized to Asia/Kolkata
    naive_dt = datetime.datetime(2026, 8, 17, 10, 30)
    norm_dt = normalization_service.normalize_timestamp(naive_dt)
    assert norm_dt.tzinfo is not None
    assert norm_dt.tzinfo.zone == "Asia/Kolkata"

    # ISO string timestamp
    iso_str = "2026-08-17T10:30:00Z"
    norm_iso = normalization_service.normalize_timestamp(iso_str)
    assert norm_iso.tzinfo is not None

def test_quote_dict_normalization():
    raw = {
        "symbol": "nifty 50",
        "ltp": "24500.555",
        "open": 24450.0,
        "high": 24520.0,
        "low": 24400.0,
        "close": 24500.0,
        "volume": "100000"
    }
    norm = normalization_service.normalize_quote_dict(raw)
    assert norm["symbol"] == "NIFTY"
    assert norm["ltp"] == 24500.56
    assert norm["volume"] == 100000
    assert norm["provider"] == "mock"
