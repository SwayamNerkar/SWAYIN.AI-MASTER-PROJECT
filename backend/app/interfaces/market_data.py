import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from app.schemas.market_data import IndexQuote, OHLCVCandle, MarketSnapshot

class MarketDataInterface(ABC):
    """
    Abstract Market Data Provider Interface.
    Decouples feature engine, ML, and dashboard from specific market data providers.
    Supports NIFTY 50 and SENSEX symbols natively.
    """

    @abstractmethod
    async def get_index_quote(self, symbol: str) -> IndexQuote:
        """Returns normalized spot quote for index symbol ('NIFTY' or 'SENSEX')."""
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None
    ) -> List[OHLCVCandle]:
        """Returns normalized OHLCV candles for given symbol and timeframe ('1m', '5m')."""
        pass

    @abstractmethod
    async def get_latest_candle(self, symbol: str, timeframe: str = "1m") -> OHLCVCandle:
        """Returns the most recent single OHLCV candle for a symbol."""
        pass

    @abstractmethod
    async def get_market_snapshot(self) -> MarketSnapshot:
        """Returns unified market snapshot for NIFTY, SENSEX, and session state."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Returns market data provider health status."""
        pass
