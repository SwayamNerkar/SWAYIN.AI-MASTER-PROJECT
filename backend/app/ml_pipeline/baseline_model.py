import os
import joblib
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor

from app.interfaces.ml import MLModelInterface
from app.core.config import settings

logger = logging.getLogger("swayin")

class GradientBoostingModel(MLModelInterface):
    """
    Baseline ML Regression Model wrapping Scikit-Learn GradientBoostingRegressor.
    Predicts future_return = (close[t + horizon] - close[t]) / close[t].
    """

    def __init__(
        self,
        n_estimators: int = 100,
        learning_rate: float = 0.05,
        max_depth: int = 3,
        random_state: int = settings.ML_RANDOM_SEED
    ):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.random_state = random_state
        self.model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=random_state
        )
        self.is_fitted = False

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        self.model.fit(X, y)
        self.is_fitted = True
        logger.info(f"Fitted GradientBoostingRegressor on {len(X)} training samples.")

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("Model is not fitted! Call fit(X, y) or load(path) before predict(X).")
        return self.model.predict(X)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)
        logger.info(f"Saved model artifact to {path}")

    def load(self, path: str) -> None:
        self.model = joblib.load(path)
        self.is_fitted = True
        logger.info(f"Loaded model artifact from {path}")
