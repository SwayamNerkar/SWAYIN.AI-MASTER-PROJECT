import logging
import datetime
from typing import List, Dict, Any, Optional

from app.core.session_engine import session_engine, SessionState
from app.services.market_data_service import market_data_service
from app.services.feature_service import feature_service
from app.engines.regime_engine import MarketRegimeEngine, regime_engine
from app.schemas.regime import MarketRegimeSnapshot, RegimeHistoryResponse, DirectionalRegime, VolatilityState

logger = logging.getLogger("swayin")

class MarketRegimeService:
    """
    Coordinator Service for Market Regime & Volatility State Machine.
    Connects validated features to regime classification and session lifecycle.
    """

    def __init__(self, engine: Optional[MarketRegimeEngine] = None):
        self.engine = engine or regime_engine

    async def get_market_regime(self, symbol: str, timeframe: str = "1m") -> MarketRegimeSnapshot:
        """
        Calculates and returns current MarketRegimeSnapshot for a symbol.
        """
        candles = await market_data_service.get_ohlcv(symbol, timeframe=timeframe, limit=50)
        snapshots = feature_service.generate_feature_series(candles, timeframe=timeframe)
        
        if not snapshots:
            now = datetime.datetime.now(feature_service.IST)
            return MarketRegimeSnapshot(
                symbol=symbol.upper(),
                timestamp=now,
                timeframe=timeframe,
                directional_regime=DirectionalRegime.SIDEWAYS,
                volatility_state=VolatilityState.MEDIUM,
                confidence=0.5,
                reasons=["INSUFFICIENT_DATA"],
                feature_timestamp=now,
                session_state="SESSION_CLOSED",
                validity_status="UNAVAILABLE",
                data_mode="MOCK / SIMULATED DATA",
                provider="mock"
            )

        regimes = self.engine.classify_regime_series(snapshots)
        latest_regime = regimes[-1]
        
        # Session state overlay
        session_info = session_engine.get_session_info()
        s_state = session_info["state"]
        latest_regime.session_state = s_state
        
        if s_state in (SessionState.PRE_MARKET.value, SessionState.WARMUP.value):
            latest_regime.validity_status = "WARMUP"
        elif s_state == SessionState.SESSION_CLOSED.value:
            latest_regime.validity_status = "SESSION_CLOSED"
        else:
            latest_regime.validity_status = "VALID" if snapshots[-1].warmup_ready else "WARMUP"

        return latest_regime

    async def get_regime_history(self, symbol: str, timeframe: str = "1m", limit: int = 50) -> RegimeHistoryResponse:
        """
        Calculates and returns chronological series of regime snapshots & volatility transitions.
        """
        candles = await market_data_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
        snapshots = feature_service.generate_feature_series(candles, timeframe=timeframe)
        regimes = self.engine.classify_regime_series(snapshots)
        transitions = self.engine.vol_machine.transition_history

        return RegimeHistoryResponse(
            symbol=symbol.upper(),
            timeframe=timeframe,
            total_snapshots=len(regimes),
            snapshots=regimes,
            transitions=transitions
        )

regime_service = MarketRegimeService()
