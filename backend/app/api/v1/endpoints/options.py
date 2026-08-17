from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from app.services.market_data_service import market_data_service
from app.services.validation_service import MarketDataValidationError
from app.schemas.market_data import ValidatedOptionChain

router = APIRouter()

@router.get("/nifty", response_model=ValidatedOptionChain)
async def get_nifty_option_chain(expiry: Optional[str] = Query(None, description="Expiry date YYYY-MM-DD")):
    try:
        return await market_data_service.get_validated_option_chain("NIFTY", expiry=expiry)
    except MarketDataValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Option chain validation failed: {str(ve)}")

@router.get("/sensex", response_model=ValidatedOptionChain)
async def get_sensex_option_chain(expiry: Optional[str] = Query(None, description="Expiry date YYYY-MM-DD")):
    try:
        return await market_data_service.get_validated_option_chain("SENSEX", expiry=expiry)
    except MarketDataValidationError as ve:
        raise HTTPException(status_code=422, detail=f"Option chain validation failed: {str(ve)}")
