from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from app.schemas.ml import PredictionResponse, ModelMetadata, ModelMetrics

class MLModelInterface(ABC):
    """
    Abstract Interface for Machine Learning Prediction Models.
    Decouples application logic from underlying framework (scikit-learn, PyTorch, etc.).
    """

    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Trains model on feature matrix X and target y."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions for feature matrix X."""
        pass

    @abstractmethod
    def save(self, path: str) -> None:
        """Serializes trained model artifact to path."""
        pass

    @abstractmethod
    def load(self, path: str) -> None:
        """Loads serialized model artifact from path."""
        pass

class DatasetBuilderInterface(ABC):
    @abstractmethod
    def build_dataset(
        self,
        symbol: str,
        timeframe: str = "1m",
        horizon: int = 3
    ) -> Tuple[pd.DataFrame, List[str], str]:
        """Constructs dataset with feature matrix and target column."""
        pass

class PredictionServiceInterface(ABC):
    @abstractmethod
    async def predict_latest(self, symbol: str, timeframe: str = "1m") -> PredictionResponse:
        """Generates latest prediction for symbol and timeframe."""
        pass
