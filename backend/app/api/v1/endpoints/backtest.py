from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, Dict, Any

from app.schemas.backtest import BacktestConfig, BacktestResult, BacktestListResponse
from app.services.backtest_service import backtest_service

router = APIRouter()

@router.post("/run", response_model=BacktestResult)
async def run_backtest_endpoint(
    config: BacktestConfig = Body(...)
):
    """
    Triggers walk-forward prediction evaluation backtest on historical/mock market data.
    Evaluates ML model return forecasts against actual outcomes with zero future leakage.
    """
    try:
        return await backtest_service.run_backtest(config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")

@router.get("", response_model=BacktestListResponse)
async def list_backtests_endpoint():
    """
    Returns a summary list of recent backtest evaluation runs.
    """
    try:
        return backtest_service.list_backtests()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backtests: {str(e)}")

@router.get("/{backtest_id}", response_model=BacktestResult)
async def get_backtest_endpoint(backtest_id: str):
    """
    Returns the complete walk-forward evaluation report for a specific backtest ID.
    """
    res = backtest_service.get_backtest(backtest_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Backtest run '{backtest_id}' not found.")
    return res

@router.get("/{backtest_id}/predictions")
async def get_backtest_predictions_endpoint(
    backtest_id: str,
    offset: int = Query(0, ge=0, description="Pagination offset index"),
    limit: int = Query(50, ge=1, le=500, description="Pagination page limit size")
):
    """
    Returns paginated prediction vs actual records for a specific backtest ID.
    """
    res = backtest_service.get_backtest(backtest_id)
    if not res:
        raise HTTPException(status_code=404, detail=f"Backtest run '{backtest_id}' not found.")
    return backtest_service.get_backtest_predictions(backtest_id, offset=offset, limit=limit)
