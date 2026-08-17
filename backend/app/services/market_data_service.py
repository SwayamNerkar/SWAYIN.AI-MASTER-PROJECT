import datetime
import logging
from typing import Dict, Any, List, Optional
import pytz

from app.core.config import settings
from app.core.session_engine import session_engine
from app.schemas.market_data import (
    IndexQuote, OHLCVCandle, DataHealthStatus, MarketSnapshot, ValidatedOptionChain
)
from app.services.normalization_service import normalization_service
from app.services.validation_service import validation_service, MarketDataValidationError
from app.services.caching_service import cache_service
from app.adapters.mock.mock_feed import MockMarketDataAdapter
from app.adapters.mock.mock_option_chain import MockOptionChainAdapter

logger = logging.getLogger("swayin")

class MarketDataService:
    """
    Core Production Market Data Coordinator Service.
    Obtains, normalizes, validates, caches, checks freshness, and persists market data.
    """

    IST = pytz.timezone("Asia/Kolkata")

    def __init__(
        self,
        provider_adapter: Optional[Any] = None,
        option_adapter: Optional[Any] = None,
        freshness_threshold: float = settings.MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS
    ):
        self.feed_adapter = provider_adapter or MockMarketDataAdapter()
        self.option_adapter = option_adapter or MockOptionChainAdapter(feed=self.feed_adapter)
        self.freshness_threshold = freshness_threshold

    def calculate_data_freshness(self, timestamp: datetime.datetime) -> tuple[float, bool]:
        """
        Calculates data age in seconds and checks if it satisfies the freshness threshold.
        """
        now = datetime.datetime.now(self.IST)
        if timestamp.tzinfo is None:
            timestamp = self.IST.localize(timestamp)
        else:
            timestamp = timestamp.astimezone(self.IST)

        age_seconds = max(0.0, round((now - timestamp).total_seconds(), 2))
        is_fresh = (age_seconds <= self.freshness_threshold)
        return age_seconds, is_fresh

    async def get_index_quote(self, symbol: str, use_cache: bool = True) -> IndexQuote:
        """
        Obtains, normalizes, validates, and checks freshness for an IndexQuote.
        """
        sym = normalization_service.normalize_symbol(symbol)
        cache_key = f"market:quote:{sym}"

        if use_cache:
            cached_quote = await cache_service.get(cache_key)
            if cached_quote and isinstance(cached_quote, IndexQuote):
                # Update freshness age dynamically
                age, is_fresh = self.calculate_data_freshness(cached_quote.timestamp)
                cached_quote.data_age_seconds = age
                cached_quote.is_fresh = is_fresh
                return cached_quote

        raw_quote = await self.feed_adapter.get_index_quote(sym)
        normalized_dict = normalization_service.normalize_quote_dict(raw_quote, provider="mock")
        
        quote = IndexQuote(**normalized_dict)
        
        # Calculate freshness
        age, is_fresh = self.calculate_data_freshness(quote.timestamp)
        quote.data_age_seconds = age
        quote.is_fresh = is_fresh

        if not is_fresh:
            logger.warning(f"STALE DATA WARNING: Quote for {sym} is {age}s old (threshold: {self.freshness_threshold}s)")

        # Validate quote structure
        validation_service.validate_quote(quote)

        # Cache valid quote
        await cache_service.set(cache_key, quote, ttl_seconds=3.0)

        return quote

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100
    ) -> List[OHLCVCandle]:
        """
        Obtains, normalizes, and validates OHLCV candle series.
        """
        sym = normalization_service.normalize_symbol(symbol)
        interval = normalization_service.normalize_interval(timeframe)
        cache_key = f"market:ohlcv:{sym}:{interval}:{limit}"

        cached_bars = await cache_service.get(cache_key)
        if cached_bars and isinstance(cached_bars, list):
            return cached_bars

        raw_bars = await self.feed_adapter.get_ohlcv(sym, timeframe=interval, limit=limit)
        
        candles = []
        for raw_bar in raw_bars:
            norm_dict = normalization_service.normalize_candle_dict(raw_bar, provider="mock")
            candle = OHLCVCandle(**norm_dict)
            candles.append(candle)

        # Validate series integrity
        validation_service.validate_candle_series(candles)

        await cache_service.set(cache_key, candles, ttl_seconds=5.0)

        return candles

    async def get_latest_candle(self, symbol: str, timeframe: str = "1m") -> OHLCVCandle:
        """Returns the most recent validated candle for a symbol."""
        bars = await self.get_ohlcv(symbol, timeframe=timeframe, limit=1)
        if not bars:
            raise MarketDataValidationError(f"No OHLCV bars returned for {symbol}")
        return bars[-1]

    async def get_market_snapshot(self) -> MarketSnapshot:
        """
        Generates a unified, normalized, validated MarketSnapshot with full data health metrics.
        """
        cache_key = "market:snapshot"
        cached_snapshot = await cache_service.get(cache_key)
        if cached_snapshot and isinstance(cached_snapshot, MarketSnapshot):
            # Recalculate dynamic age
            nifty_age, nifty_fresh = self.calculate_data_freshness(cached_snapshot.nifty.timestamp)
            sensex_age, sensex_fresh = self.calculate_data_freshness(cached_snapshot.sensex.timestamp)
            cached_snapshot.data_health.nifty_age_seconds = nifty_age
            cached_snapshot.data_health.nifty_fresh = nifty_fresh
            cached_snapshot.data_health.sensex_age_seconds = sensex_age
            cached_snapshot.data_health.sensex_fresh = sensex_fresh
            cached_snapshot.data_health.stale_warning = (not nifty_fresh or not sensex_fresh)
            return cached_snapshot

        nifty_quote = await self.get_index_quote("NIFTY", use_cache=False)
        sensex_quote = await self.get_index_quote("SENSEX", use_cache=False)
        session_info = session_engine.get_session_info()

        nifty_age, nifty_fresh = self.calculate_data_freshness(nifty_quote.timestamp)
        sensex_age, sensex_fresh = self.calculate_data_freshness(sensex_quote.timestamp)
        
        stale_warning = (not nifty_fresh or not sensex_fresh)

        data_health = DataHealthStatus(
            nifty_fresh=nifty_fresh,
            sensex_fresh=sensex_fresh,
            nifty_age_seconds=nifty_age,
            sensex_age_seconds=sensex_age,
            freshness_threshold_seconds=self.freshness_threshold,
            validation_passed=True,
            stale_warning=stale_warning,
            provider_healthy=True
        )

        now = datetime.datetime.now(self.IST)

        snapshot = MarketSnapshot(
            timestamp=now,
            session_state=session_info["state"],
            nifty=nifty_quote,
            sensex=sensex_quote,
            data_health=data_health,
            provider_status={
                "provider": settings.MARKET_DATA_PROVIDER,
                "data_mode": "MOCK / SIMULATED DATA",
                "cache_enabled": settings.MARKET_DATA_CACHE_ENABLED,
                "is_operational": True
            }
        )

        await cache_service.set(cache_key, snapshot, ttl_seconds=2.0)

        return snapshot

    async def get_validated_option_chain(self, underlying: str, expiry: Optional[str] = None) -> ValidatedOptionChain:
        """
        Obtains, validates, and returns an Option Chain snapshot.
        """
        sym = normalization_service.normalize_symbol(underlying)
        cache_key = f"options:chain:{sym}:{expiry or 'default'}"

        cached_chain = await cache_service.get(cache_key)
        if cached_chain and isinstance(cached_chain, ValidatedOptionChain):
            return cached_chain

        raw_chain = await self.option_adapter.get_option_chain(sym, expiry=expiry)
        
        # Validate chain data
        validation_service.validate_option_chain(raw_chain)

        ts = normalization_service.normalize_timestamp(raw_chain.get("timestamp"))

        chain_obj = ValidatedOptionChain(
            underlying=sym,
            spot_price=float(raw_chain["spot_price"]),
            atm_strike=float(raw_chain["atm_strike"]),
            expiry_date=str(raw_chain["expiry_date"]),
            lot_size=int(raw_chain["lot_size"]),
            pcr_oi=float(raw_chain["pcr_oi"]),
            total_ce_oi=int(raw_chain["total_ce_oi"]),
            total_pe_oi=int(raw_chain["total_pe_oi"]),
            chain=raw_chain["chain"],
            timestamp=ts,
            data_mode="MOCK / SIMULATED DATA",
            provider="mock",
            is_validated=True
        )

        await cache_service.set(cache_key, chain_obj, ttl_seconds=3.0)

        return chain_obj

market_data_service = MarketDataService()
