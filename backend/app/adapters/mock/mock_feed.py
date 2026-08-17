import random
import datetime
from typing import Dict, Any, List, Optional
import pytz

from app.interfaces.market_data import MarketDataInterface
from app.schemas.market_data import IndexQuote, OHLCVCandle, MarketSnapshot, DataHealthStatus
from app.core.session_engine import session_engine

class MockMarketDataAdapter(MarketDataInterface):
    """
    Deterministic Synthetic Market Data Feed Generator.
    Supports NIFTY 50 and SENSEX intraday OHLCV bars for 1m and 5m timeframes.
    Explicitly labeled as MOCK / SIMULATED DATA.
    """

    IST = pytz.timezone("Asia/Kolkata")

    BASE_PRICES = {
        "NIFTY": 24500.0,
        "SENSEX": 80100.0,
        "INDIAVIX": 14.5
    }

    def __init__(self, seed: Optional[int] = 42):
        self.seed = seed
        self.rng = random.Random(seed)

    async def get_index_quote(self, symbol: str) -> Dict[str, Any]:
        """Returns dict quote for backward compatibility with Task 1.1 and normalization service."""
        sym = symbol.upper()
        if sym not in self.BASE_PRICES:
            sym = "NIFTY"
            
        base = self.BASE_PRICES[sym]
        variation = self.rng.uniform(-0.005, 0.005) * base
        ltp = round(base + variation, 2)
        
        now = datetime.datetime.now(self.IST)
        
        return {
            "symbol": sym,
            "ltp": ltp,
            "change": round(variation, 2),
            "change_percent": round((variation / base) * 100, 2),
            "open": round(base * 0.998, 2),
            "high": round(base * 1.004, 2),
            "low": round(base * 0.995, 2),
            "close": round(base, 2),
            "previous_close": round(base, 2),
            "volume": self.rng.randint(5000000, 15000000),
            "timestamp": now.isoformat(),
            "data_mode": "MOCK / SIMULATED DATA",
            "provider": "mock",
            "timezone": "Asia/Kolkata",
            "is_simulated": True
        }

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
        start: Optional[datetime.datetime] = None,
        end: Optional[datetime.datetime] = None
    ) -> List[Dict[str, Any]]:
        """Returns raw candle dicts for normalization service."""
        sym = symbol.upper()
        base_price = self.BASE_PRICES.get(sym, 24500.0)
        
        minutes_step = 5 if timeframe == "5m" else 1
        now = datetime.datetime.now(self.IST).replace(second=0, microsecond=0)
        start_time = now - datetime.timedelta(minutes=minutes_step * limit)
        
        bars = []
        current_close = base_price
        
        # Local deterministic RNG for OHLC series reproducibility
        local_rng = random.Random(self.seed or 42)
        
        for i in range(limit):
            bar_time = start_time + datetime.timedelta(minutes=minutes_step * i)
            # Intraday random walk with slight mean reversion
            change_pct = local_rng.normalvariate(0, 0.0012)
            open_p = current_close
            close_p = open_p * (1 + change_pct)
            
            high_p = max(open_p, close_p) * (1 + abs(local_rng.uniform(0, 0.0008)))
            low_p = min(open_p, close_p) * (1 - abs(local_rng.uniform(0, 0.0008)))
            volume = local_rng.randint(20000, 180000)
            
            bars.append({
                "timestamp": bar_time.isoformat(),
                "symbol": sym,
                "interval": timeframe,
                "timeframe": timeframe,
                "open": round(open_p, 2),
                "high": round(high_p, 2),
                "low": round(low_p, 2),
                "close": round(close_p, 2),
                "volume": volume,
                "data_mode": "MOCK / SIMULATED DATA",
                "provider": "mock"
            })
            current_close = close_p
            
        return bars

    async def get_latest_candle(self, symbol: str, timeframe: str = "1m") -> Dict[str, Any]:
        bars = await self.get_ohlcv(symbol, timeframe=timeframe, limit=1)
        return bars[-1]

    async def get_market_snapshot(self) -> Dict[str, Any]:
        nifty = await self.get_index_quote("NIFTY")
        sensex = await self.get_index_quote("SENSEX")
        session_info = session_engine.get_session_info()

        return {
            "timestamp": datetime.datetime.now(self.IST).isoformat(),
            "data_mode": "MOCK / SIMULATED DATA",
            "session_state": session_info["state"],
            "snapshot": {
                "NIFTY": nifty,
                "SENSEX": sensex
            }
        }

    async def health_check(self) -> Dict[str, Any]:
        return {
            "provider": "MOCK_MARKET_DATA_FEED",
            "is_connected": True,
            "status": "OPERATIONAL",
            "data_mode": "MOCK / SIMULATED DATA"
        }
