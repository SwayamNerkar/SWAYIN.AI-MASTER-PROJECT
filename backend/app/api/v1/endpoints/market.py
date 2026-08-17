from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.services.market_data_service import market_data_service
from app.services.validation_service import MarketDataValidationError
from app.core.session_engine import session_engine
from app.schemas.market_data import MarketSnapshot

router = APIRouter()

@router.get("/status")
async def get_market_status():
    session_info = session_engine.get_session_info()
    snapshot = await market_data_service.get_market_snapshot()
    
    return {
        "market": "NSE/BSE",
        "timezone": "Asia/Kolkata",
        "state": session_info["state"],
        "is_trading_day": session_info["is_trading_day"],
        "is_market_open": session_info["is_market_open"],
        "new_trades_allowed": session_info["new_trades_allowed"],
        "exit_monitoring": session_info["exit_monitoring_active"],
        "next_transition": session_info["next_transition"],
        "message": session_info["message"],
        "data_health": snapshot.data_health,
        "timestamp": session_info["current_time_ist"]
    }

@router.get("/session")
async def get_market_session():
    return session_engine.get_session_info()

@router.get("/snapshot", response_model=MarketSnapshot)
async def get_market_snapshot():
    """
    Returns unified, normalized, and validated composite Market Snapshot.
    Exposes NIFTY, SENSEX, session state, and data freshness metrics.
    """
    try:
        return await market_data_service.get_market_snapshot()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate market snapshot: {str(e)}")

@router.get("/nifty")
async def get_nifty_data(timeframe: str = Query("1m", pattern="^(1m|5m)$"), limit: int = Query(50, ge=1, le=500)):
    try:
        quote = await market_data_service.get_index_quote("NIFTY")
        ohlcv = await market_data_service.get_ohlcv("NIFTY", timeframe=timeframe, limit=limit)
        return {
            "quote": quote,
            "ohlcv": ohlcv
        }
    except MarketDataValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Data validation error for NIFTY: {str(ve)}")

@router.get("/sensex")
async def get_sensex_data(timeframe: str = Query("1m", pattern="^(1m|5m)$"), limit: int = Query(50, ge=1, le=500)):
    try:
        quote = await market_data_service.get_index_quote("SENSEX")
        ohlcv = await market_data_service.get_ohlcv("SENSEX", timeframe=timeframe, limit=limit)
        return {
            "quote": quote,
            "ohlcv": ohlcv
        }
    except MarketDataValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Data validation error for SENSEX: {str(ve)}")
