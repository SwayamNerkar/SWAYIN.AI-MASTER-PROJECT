from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional

from app.services.market_data_service import market_data_service
from app.services.feature_service import feature_service
from app.schemas.features import FeatureSnapshot, FeatureMetadata, FeatureSeriesResponse

router = APIRouter()

@router.get("/metadata", response_model=List[FeatureMetadata])
async def get_feature_metadata():
    """
    Returns complete metadata registry for all supported technical indicators and features.
    """
    return feature_service.get_feature_metadata()

@router.get("/nifty", response_model=FeatureSeriesResponse)
async def get_nifty_features(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')"),
    limit: int = Query(50, ge=10, le=200, description="Number of bars to calculate features for")
):
    """
    Generates and returns normalized feature snapshot series for NIFTY 50.
    Calculated strictly without look-ahead bias.
    """
    try:
        candles = await market_data_service.get_ohlcv("NIFTY", timeframe=timeframe, limit=limit)
        snapshots = feature_service.generate_feature_series(candles, timeframe=timeframe)
        
        return FeatureSeriesResponse(
            symbol="NIFTY",
            timeframe=timeframe,
            total_snapshots=len(snapshots),
            warmup_period_bars=feature_service.WARMUP_BARS_REQUIRED,
            snapshots=snapshots,
            metadata=feature_service.get_feature_metadata()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate features for NIFTY: {str(e)}")

@router.get("/sensex", response_model=FeatureSeriesResponse)
async def get_sensex_features(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')"),
    limit: int = Query(50, ge=10, le=200, description="Number of bars to calculate features for")
):
    """
    Generates and returns normalized feature snapshot series for SENSEX.
    Calculated strictly without look-ahead bias.
    """
    try:
        candles = await market_data_service.get_ohlcv("SENSEX", timeframe=timeframe, limit=limit)
        snapshots = feature_service.generate_feature_series(candles, timeframe=timeframe)
        
        return FeatureSeriesResponse(
            symbol="SENSEX",
            timeframe=timeframe,
            total_snapshots=len(snapshots),
            warmup_period_bars=feature_service.WARMUP_BARS_REQUIRED,
            snapshots=snapshots,
            metadata=feature_service.get_feature_metadata()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate features for SENSEX: {str(e)}")
