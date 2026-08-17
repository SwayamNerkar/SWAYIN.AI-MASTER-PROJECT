from fastapi import APIRouter
from app.core.config import settings
from app.core.session_engine import session_engine

router = APIRouter()

@router.get("/health")
async def get_health():
    session_info = session_engine.get_session_info()
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
        "timezone": settings.TIMEZONE,
        "data_feed_mode": settings.DATA_FEED_MODE,
        "broker_adapter": settings.BROKER_ADAPTER,
        "paper_trading_enabled": settings.PAPER_TRADING_ENABLED,
        "market_state": session_info["state"],
        "timestamp_ist": session_info["current_time_ist"]
    }
