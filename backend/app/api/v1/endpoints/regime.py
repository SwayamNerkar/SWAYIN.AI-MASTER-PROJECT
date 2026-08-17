from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.services.regime_service import regime_service
from app.schemas.regime import MarketRegimeSnapshot, RegimeHistoryResponse

router = APIRouter()

@router.get("/nifty", response_model=MarketRegimeSnapshot)
async def get_nifty_regime(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')")
):
    """
    Returns the current Market Regime and Volatility State snapshot for NIFTY 50.
    """
    try:
        return await regime_service.get_market_regime("NIFTY", timeframe=timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate NIFTY regime: {str(e)}")

@router.get("/sensex", response_model=MarketRegimeSnapshot)
async def get_sensex_regime(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')")
):
    """
    Returns the current Market Regime and Volatility State snapshot for SENSEX.
    """
    try:
        return await regime_service.get_market_regime("SENSEX", timeframe=timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to evaluate SENSEX regime: {str(e)}")

@router.get("/nifty/history", response_model=RegimeHistoryResponse)
async def get_nifty_regime_history(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')"),
    limit: int = Query(50, ge=10, le=200, description="Number of bars to calculate regime history for")
):
    """
    Returns historical series of Market Regime snapshots and Volatility State transitions for NIFTY 50.
    """
    try:
        return await regime_service.get_regime_history("NIFTY", timeframe=timeframe, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch NIFTY regime history: {str(e)}")

@router.get("/sensex/history", response_model=RegimeHistoryResponse)
async def get_sensex_regime_history(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')"),
    limit: int = Query(50, ge=10, le=200, description="Number of bars to calculate regime history for")
):
    """
    Returns historical series of Market Regime snapshots and Volatility State transitions for SENSEX.
    """
    try:
        return await regime_service.get_regime_history("SENSEX", timeframe=timeframe, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch SENSEX regime history: {str(e)}")
