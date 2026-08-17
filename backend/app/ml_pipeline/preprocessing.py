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
        if not self.feature_list:
            self.feature_list = sorted(list(X_train.columns))
        
        X_sub = X_train[self.feature_list]
        X_imp = self.imputer.fit_transform(X_sub)
        self.scaler.fit(X_imp)
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not self.is_fitted:
            raise ValueError("FeaturePreprocessor is not fitted! Call fit(X_train) first.")
        
        X_sub = X[self.feature_list]
        X_imp = self.imputer.transform(X_sub)
        X_scaled = self.scaler.transform(X_imp)
        return pd.DataFrame(X_scaled, columns=self.feature_list, index=X.index)

    def save(self, filepath: str) -> None:
        """Saves fitted preprocessor object using joblib."""
        import joblib
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump(self, filepath)

    def load(self, filepath: str) -> "FeaturePreprocessor":
        """Loads fitted preprocessor object using joblib."""
        import joblib
        obj = joblib.load(filepath)
        self.feature_list = obj.feature_list
        self.imputer = obj.imputer
        self.scaler = obj.scaler
        self.is_fitted = obj.is_fitted
        return self
