from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.schemas.market_data import OHLCVCandle
from app.schemas.features import FeatureSnapshot, FeatureMetadata

class FeatureEngineeringInterface(ABC):
    """
    Abstract Interface for Feature Engineering Subsystem.
    Decouples Technical Indicators & Feature calculations from ML Models & Strategies.
    """

    @abstractmethod
    def generate_features(self, candles: List[OHLCVCandle], timeframe: str = "1m") -> FeatureSnapshot:
        """Generates feature snapshot for the latest candle in series."""
        pass

    @abstractmethod
    def generate_feature_series(self, candles: List[OHLCVCandle], timeframe: str = "1m") -> List[FeatureSnapshot]:
        """Generates a historical time series of feature snapshots without look-ahead bias."""
        pass

    @abstractmethod
    def validate_features(self, snapshot: FeatureSnapshot) -> bool:
        """Validates feature bounds, NaNs, and warmup readiness."""
        pass

    @abstractmethod
    def get_feature_metadata(self) -> List[FeatureMetadata]:
        """Returns metadata definitions for all calculated features."""
        pass
