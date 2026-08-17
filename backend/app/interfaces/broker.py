from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BrokerInterface(ABC):
    """
    Abstract Interface for Broker Adapters.
    Prevents lock-in to Groww or any single broker.
    All strategies, risk engines, and UI controllers interact exclusively with this contract.
    """

    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Returns account information and status."""
        pass

    @abstractmethod
    async def get_available_capital(self) -> float:
        """Returns available unencumbered funds for trading (in INR)."""
        pass

    @abstractmethod
    async def get_positions(self) -> List[Dict[str, Any]]:
        """Returns active open positions."""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Returns execution status for a given order ID."""
        pass

    @abstractmethod
    async def get_ltp(self, symbol: str) -> float:
        """Returns current Last Traded Price (LTP) for an index or option contract."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Returns detailed quote with bid/ask depth, volume, and OHLC."""
        pass

    @abstractmethod
    async def place_order(self, order_req: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method for order placement.
        Must be paper-traded or blocked in initial versions.
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Abstract method to cancel an open order."""
        pass
