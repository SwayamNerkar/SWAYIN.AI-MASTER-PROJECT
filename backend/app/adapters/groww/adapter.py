import logging
from typing import Dict, Any, List
from app.interfaces.broker import BrokerInterface

logger = logging.getLogger("swayin")

class GrowwAdapter(BrokerInterface):
    """
    STUB Adapter for Future Groww Integration.
    
    IMPORTANT SAFETY RULE:
    - This is currently a non-operational STUB.
    - DOES NOT connect to real Groww APIs.
    - DOES NOT require real API credentials.
    - DOES NOT place real orders.
    
    All methods raise NotImplementedError or return non-operational status to guarantee safety.
    """

    def __init__(self, api_key: str = "", api_secret: str = ""):
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("GrowwAdapter initialized in STUB mode. Real execution disabled.")

    async def get_account_info(self) -> Dict[str, Any]:
        return {
            "broker_name": "GROWW",
            "status": "STUB_NOT_CONNECTED",
            "message": "Groww adapter is currently a stub. Real broker credentials are not connected.",
            "is_connected": False
        }

    async def get_available_capital(self) -> float:
        raise NotImplementedError("Groww API integration is not active yet. Use MockBrokerAdapter.")

    async def get_positions(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Groww API integration is not active yet. Use MockBrokerAdapter.")

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        raise NotImplementedError("Groww API integration is not active yet. Use MockBrokerAdapter.")

    async def get_ltp(self, symbol: str) -> float:
        raise NotImplementedError("Groww live data feed is not connected yet. Use MockMarketDataAdapter.")

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError("Groww live data feed is not connected yet. Use MockMarketDataAdapter.")

    async def place_order(self, order_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        SAFETY GUARDRAIL: Real order placement is strictly disabled.
        """
        logger.warning(f"BLOCKED: Attempted to place order via GrowwAdapter STUB: {order_req}")
        return {
            "order_id": "DISABLED",
            "status": "REJECTED",
            "reason": "SAFETY_RULE: Groww live execution is disabled. Use MockBrokerAdapter for paper trading."
        }

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return {
            "order_id": order_id,
            "status": "REJECTED",
            "reason": "SAFETY_RULE: Groww live execution is disabled."
        }

"""
FUTURE GROWW INTEGRATION ROADMAP (TODO):
1. OAuth2 / API Key authentication flow handling & token refresh worker.
2. Groww Market Data WebSocket stream handler for live NIFTY/SENSEX quotes & Option Chain ticks.
3. Order placement, modification, and cancellation via official Groww API endpoints.
4. Real-time order update callback webhook listener for fill notifications.
5. Margin & funds query adapter mapping Groww wallet balance to BrokerInterface.
"""
