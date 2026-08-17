from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional

from app.schemas.ml import PredictionResponse, ModelMetadata
from app.ml_pipeline.prediction_service import prediction_service
from app.ml_pipeline.training_service import training_service

router = APIRouter()

@router.get("/nifty", response_model=PredictionResponse)
async def get_nifty_prediction(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')")
):
    """
    Returns the current ML model prediction for NIFTY 50.
    Pure numerical prediction metric — NOT a trading recommendation or signal.
    """
    try:
        return await prediction_service.predict_latest("NIFTY", timeframe=timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate NIFTY prediction: {str(e)}")

@router.get("/sensex", response_model=PredictionResponse)
async def get_sensex_prediction(
    timeframe: str = Query("1m", pattern="^(1m|5m)$", description="Candle timeframe ('1m' or '5m')")
):
    """
    Returns the current ML model prediction for SENSEX.
    Pure numerical prediction metric — NOT a trading recommendation or signal.
    """
    try:
        return await prediction_service.predict_latest("SENSEX", timeframe=timeframe)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SENSEX prediction: {str(e)}")

@router.post("/train", response_model=ModelMetadata)
async def train_model_endpoint(
    symbol: str = Query("NIFTY", description="Symbol e.g. 'NIFTY' or 'SENSEX'"),
    timeframe: str = Query("1m", description="Timeframe e.g. '1m' or '5m'"),
    horizon: int = Query(3, ge=1, le=10, description="Prediction horizon in bars")
):
    """
    Controlled development endpoint to train baseline ML model artifact.
    """
    try:
        metadata, _, _ = await training_service.train_model(
            symbol=symbol.upper(), timeframe=timeframe, horizon=horizon
        )
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model training failed: {str(e)}")
