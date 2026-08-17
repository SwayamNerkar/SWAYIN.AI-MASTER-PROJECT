import json
import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

logger = logging.getLogger("swayin")

class FeaturePreprocessor:
    """
    Production Feature Preprocessor.
    Applies missing-value imputation and feature scaling.
    MANDATORY RULE: Imputer and Scaler are fitted ONLY on training set X_train!
    """

    def __init__(self, feature_list: Optional[List[str]] = None):
        self.feature_list = feature_list or []
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, X_train: pd.DataFrame) -> "FeaturePreprocessor":
        """Fits imputer and scaler ONLY on training feature matrix X_train."""
        if not self.feature_list:
            self.feature_list = sorted(list(X_train.columns))
        
        X_sub = X_train[self.feature_list]
        X_imp = self.imputer.fit_transform(X_sub)
        self.scaler.fit(X_imp)
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transforms input matrix using training-fitted imputer and scaler."""
        if not self.is_fitted:
            raise ValueError("FeaturePreprocessor is not fitted! Call fit(X_train) first.")
        
        # Ensure exact feature ordering
        X_sub = X[self.feature_list]
        X_imp = self.imputer.transform(X_sub)
        X_scaled = self.scaler.transform(X_imp)
        return pd.DataFrame(X_scaled, columns=self.feature_list, index=X.index)

    def save(self, filepath: str) -> None:
        """Saves preprocessing parameters to JSON file."""
        data = {
            "feature_list": self.feature_list,
            "imputer_statistics": self.imputer.statistics_.tolist(),
            "scaler_mean": self.scaler.mean_.tolist(),
            "scaler_scale": self.scaler.scale_.tolist(),
            "is_fitted": self.is_fitted
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, filepath: str) -> "FeaturePreprocessor":
        """Loads preprocessing parameters from JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)
        
        self.feature_list = data["feature_list"]
        self.is_fitted = data["is_fitted"]
        self.imputer.statistics_ = np.array(data["imputer_statistics"])
        self.scaler.mean_ = np.array(data["scaler_mean"])
        self.scaler.scale_ = np.array(data["scaler_scale"])
        self.scaler.var_ = np.square(self.scaler.scale_)
        return self
