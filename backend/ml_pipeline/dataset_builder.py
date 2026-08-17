import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np

from app.core.config import settings
from app.interfaces.ml import DatasetBuilderInterface
from app.services.market_data_service import market_data_service
from app.services.feature_service import feature_service
from app.engines.regime_engine import regime_engine

logger = logging.getLogger("swayin")

# Categorical mapping dictionaries for regime features
REGIME_MAP = {"TRENDING_UP": 1.0, "TRENDING_DOWN": -1.0, "SIDEWAYS": 0.0, "HIGH_VOLATILITY": 0.5, "REVERSAL": 2.0}
VOL_STATE_MAP = {"LOW": 0.0, "MEDIUM": 1.0, "HIGH": 2.0}

class MLDatasetBuilder(DatasetBuilderInterface):
    """
    Production ML Dataset Builder.
    Constructs timestamp-aligned feature matrices with zero look-ahead leakage.
    Generates target future_return and handles chronological dataset splitting.
    """

    def build_dataset_from_candles(
        self,
        candles: list,
        timeframe: str = "1m",
        horizon: int = settings.ML_DEFAULT_HORIZON
    ) -> Tuple[pd.DataFrame, List[str], str]:
        """
        Builds dataset from candle list.
        Returns (full_dataframe, feature_columns_list, target_column_name).
        """
        snapshots = feature_service.generate_feature_series(candles, timeframe=timeframe)
        regimes = regime_engine.classify_regime_series(snapshots)

        rows = []
        for snap, reg in zip(snapshots, regimes):
            row = {"timestamp": snap.timestamp, "close": snap.features.get("close")}
            # Feature snapshot numerical values
            row.update(snap.features)
            # Historical Regime Features (Task 1.4)
            row["regime_code"] = REGIME_MAP.get(reg.directional_regime.value, 0.0)
            row["volatility_code"] = VOL_STATE_MAP.get(reg.volatility_state.value, 1.0)
            row["regime_confidence"] = reg.confidence
            rows.append(row)

        df = pd.DataFrame(rows)
        if df.empty or len(df) <= horizon + 30:
            raise ValueError(f"Insufficient historical candles ({len(df)}) to build ML dataset (need > {horizon + 30}).")

        # Target Generation: future_return = (close[t + horizon] - close[t]) / close[t]
        target_col = "future_return"
        df[target_col] = (df["close"].shift(-horizon) - df["close"]) / df["close"]

        # Drop rows with NaN targets (the last 'horizon' rows) and warmup NaN feature rows
        df = df.dropna(subset=[target_col]).reset_index(drop=True)
        # Drop initial warmup rows (first 30)
        if len(df) > 30:
            df = df.iloc[30:].reset_index(drop=True)

        # Feature Column Selection: Exclude non-features, target, and future information
        excluded_cols = {"timestamp", "close", target_col}
        feature_cols = sorted([c for c in df.columns if c not in excluded_cols])

        return df, feature_cols, target_col

    def build_dataset(
        self,
        symbol: str,
        timeframe: str = "1m",
        horizon: int = settings.ML_DEFAULT_HORIZON
    ) -> Tuple[pd.DataFrame, List[str], str]:
        # Sync wrapper when async market data call not active
        raise NotImplementedError("Use build_dataset_async or build_dataset_from_candles")

    async def build_dataset_async(
        self,
        symbol: str,
        timeframe: str = "1m",
        horizon: int = settings.ML_DEFAULT_HORIZON,
        limit: int = 200
    ) -> Tuple[pd.DataFrame, List[str], str]:
        candles = await market_data_service.get_ohlcv(symbol, timeframe=timeframe, limit=limit)
        return self.build_dataset_from_candles(candles, timeframe=timeframe, horizon=horizon)

    @staticmethod
    def split_chronologically(
        df: pd.DataFrame,
        feature_cols: List[str],
        target_col: str,
        train_ratio: float = settings.ML_TRAIN_RATIO,
        val_ratio: float = settings.ML_VALIDATION_RATIO,
        test_ratio: float = settings.ML_TEST_RATIO
    ) -> Dict[str, Any]:
        """
        Splits dataset chronologically without random shuffling.
        Guarantees train_timestamps < val_timestamps < test_timestamps.
        """
        n = len(df)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_df = df.iloc[:train_end]
        val_df = df.iloc[train_end:val_end]
        test_df = df.iloc[val_end:]

        return {
            "X_train": train_df[feature_cols].copy(),
            "y_train": train_df[target_col].copy(),
            "train_ts": train_df["timestamp"].tolist(),
            "X_val": val_df[feature_cols].copy(),
            "y_val": val_df[target_col].copy(),
            "val_ts": val_df["timestamp"].tolist(),
            "X_test": test_df[feature_cols].copy(),
            "y_test": test_df[target_col].copy(),
            "test_ts": test_df["timestamp"].tolist()
        }

dataset_builder = MLDatasetBuilder()
