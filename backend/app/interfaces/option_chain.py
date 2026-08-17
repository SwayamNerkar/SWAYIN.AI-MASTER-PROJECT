from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class OptionChainProvider(ABC):
    """
    Abstract Interface for Option Chain Providers.
    Defines methods to fetch full option chain snapshots, strikes, IVs, and Greeks.
    """

    @abstractmethod
    async def get_option_chain(self, underlying: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        """Returns option chain structure for underlying ('NIFTY' or 'SENSEX')."""
        pass

    @abstractmethod
    async def get_atm_strike(self, underlying: str) -> float:
        """Calculates current At-The-Money (ATM) strike price."""
        pass

    @abstractmethod
    async def get_option_quote(self, option_symbol: str) -> Dict[str, Any]:
        """Returns quote for specific CE or PE option contract."""
        pass
