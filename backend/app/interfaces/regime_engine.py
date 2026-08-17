from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.features import FeatureSnapshot
from app.schemas.regime import MarketRegimeSnapshot, VolatilityState

class MarketRegimeInterface(ABC):
    """
    Abstract Interface for Market Regime & Volatility State Subsystems.
    Provides deterministic, explainable market classification for downstream engines.
    """

    @abstractmethod
    def classify_regime(self, feature_snapshot: FeatureSnapshot) -> MarketRegimeSnapshot:
        """Classifies market regime for a single feature snapshot."""
        pass

    @abstractmethod
    def classify_regime_series(self, feature_snapshots: List[FeatureSnapshot]) -> List[MarketRegimeSnapshot]:
        """Classifies chronological series of feature snapshots with stability & hysteresis."""
        pass

    @abstractmethod
    def get_volatility_state(self, feature_snapshot: FeatureSnapshot) -> VolatilityState:
        """Evaluates current Volatility State Machine state."""
        pass
