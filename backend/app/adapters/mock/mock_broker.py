import uuid
import datetime
from typing import Dict, Any, List
from app.interfaces.broker import BrokerInterface
from app.core.config import settings

class MockBrokerAdapter(BrokerInterface):
    """
    Mock / Paper Trading Broker Adapter.
    Provides safe simulation without calling any real broker API or spending real money.
    """

    def __init__(self, initial_capital: float = settings.INITIAL_CAPITAL):
        self.capital = initial_capital
        self.allocated_capital = 0.0
        self.positions: List[Dict[str, Any]] = []
        self.orders: Dict[str, Dict[str, Any]] = {}

    async def get_account_info(self) -> Dict[str, Any]:
        return {
            "broker_name": "SWAYIN_MOCK_PAPER_BROKER",
            "account_id": "PAPER_TRADER_001",
            "mode": "PAPER_TRADING",
            "total_capital": self.capital + self.allocated_capital,
            "available_capital": self.capital,
            "allocated_capital": self.allocated_capital,
            "currency": "INR",
            "is_connected": True
        }

    async def get_available_capital(self) -> float:
        return self.capital

    async def get_positions(self) -> List[Dict[str, Any]]:
        return self.positions

    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return self.orders.get(order_id, {
            "order_id": order_id,
            "status": "NOT_FOUND",
            "message": "Order ID not recognized in paper broker memory."
        })

    async def get_ltp(self, symbol: str) -> float:
        # Fallback default simulated prices
        if "SENSEX" in symbol:
            return 80150.25
        return 24530.50

    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        ltp = await self.get_ltp(symbol)
        return {
            "symbol": symbol,
            "ltp": ltp,
            "open": ltp - 25.0,
            "high": ltp + 40.0,
            "low": ltp - 30.0,
            "close": ltp - 5.0,
            "volume": 1250000,
            "bid": ltp - 0.25,
            "ask": ltp + 0.25,
            "timestamp": datetime.datetime.now().isoformat(),
            "is_simulated": True
        }

    async def place_order(self, order_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a paper/mock order.
        Explicitly labeled as MOCK_EXECUTION.
        """
        order_id = f"MOCK_ORD_{uuid.uuid4().hex[:8].upper()}"
        symbol = order_req.get("symbol", "NIFTY24500CE")
        side = order_req.get("side", "BUY")
        quantity = order_req.get("quantity", 25)
        price = order_req.get("price", 180.0)

        required_funds = price * quantity
        if side == "BUY" and required_funds > self.capital:
            return {
                "order_id": order_id,
                "status": "REJECTED",
                "reason": f"Insufficient paper capital. Required: ₹{required_funds:.2f}, Available: ₹{self.capital:.2f}"
            }

        if side == "BUY":
            self.capital -= required_funds
            self.allocated_capital += required_funds
            position = {
                "position_id": f"POS_{uuid.uuid4().hex[:6]}",
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": price,
                "current_price": price,
                "pnl": 0.0,
                "entry_time": datetime.datetime.now().isoformat()
            }
            self.positions.append(position)

        order_record = {
            "order_id": order_id,
            "status": "FILLED",
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "executed_at": datetime.datetime.now().isoformat(),
            "is_mock": True
        }
        self.orders[order_id] = order_record
        return order_record

    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        if order_id in self.orders:
            self.orders[order_id]["status"] = "CANCELLED"
            return {"order_id": order_id, "status": "CANCELLED"}
        return {"order_id": order_id, "status": "NOT_FOUND"}
