import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.market_data_service import market_data_service
from app.core.session_engine import session_engine

router = APIRouter()
logger = logging.getLogger("swayin")

@router.websocket("/ws/market")
async def market_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket streaming endpoint exposing structured event contracts:
    - MARKET_UPDATE (NIFTY & SENSEX quotes)
    - SESSION_UPDATE (Market session state machine info)
    - DATA_HEALTH_UPDATE (Data age & freshness metrics)
    """
    await websocket.accept()
    logger.info("WebSocket Client Connected: /api/v1/ws/market")
    
    try:
        while True:
            snapshot = await market_data_service.get_market_snapshot()
            session_info = session_engine.get_session_info()
            
            payload = {
                "event": "MARKET_UPDATE",
                "timestamp": snapshot.timestamp.isoformat(),
                "session_update": {
                    "event": "SESSION_UPDATE",
                    "state": session_info["state"],
                    "is_market_open": session_info["is_market_open"],
                    "new_trades_allowed": session_info["new_trades_allowed"],
                    "exit_monitoring": session_info["exit_monitoring_active"]
                },
                "data_health_update": {
                    "event": "DATA_HEALTH_UPDATE",
                    "nifty_fresh": snapshot.data_health.nifty_fresh,
                    "sensex_fresh": snapshot.data_health.sensex_fresh,
                    "nifty_age_seconds": snapshot.data_health.nifty_age_seconds,
                    "sensex_age_seconds": snapshot.data_health.sensex_age_seconds,
                    "stale_warning": snapshot.data_health.stale_warning
                },
                "nifty": snapshot.nifty.model_dump(mode="json"),
                "sensex": snapshot.sensex.model_dump(mode="json")
            }
            
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2.0)  # Stream update every 2 seconds
            
    except WebSocketDisconnect:
        logger.info("WebSocket Client Disconnected: /api/v1/ws/market")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        await websocket.close()
