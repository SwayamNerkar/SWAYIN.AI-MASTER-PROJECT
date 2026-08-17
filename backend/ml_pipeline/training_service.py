import os
import json
import uuid
import logging
import datetime
from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.core.config import settings
from app.schemas.ml import (
    ModelMetadata, ModelMetrics, ModelStatus, PredictionTarget
)
from app.ml_pipeline.dataset_builder import dataset_builder
from app.ml_pipeline.preprocessing import FeaturePreprocessor
from app.ml_pipeline.baseline_model import GradientBoostingModel

logger = logging.getLogger("swayin")

class ModelTrainingService:
    """
    Production Model Training Service.
    Orchestrates dataset creation, chronological splitting, training, evaluation,
    naive baseline comparison, versioning, and artifact persistence.
    """

    @staticmethod
    def evaluate_performance(y_true: pd.Series, y_pred: np.ndarray) -> ModelMetrics:
        """
        Calculates regression metrics (MAE, RMSE, R2, directional accuracy)
        and compares performance against a naive zero-return baseline.
        """
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        r2 = float(r2_score(y_true, y_pred)) if len(y_true) > 2 else 0.0

        # Directional Accuracy (Percentage where sign of prediction matches sign of actual return)
        correct_direction = np.sign(y_true) == np.sign(y_pred)
        dir_acc = float(np.mean(correct_direction))

        # Naive Zero-Return Baseline (predicted_return = 0)
        naive_pred = np.zeros_like(y_true)
        naive_mae = float(mean_absolute_error(y_true, naive_pred))
        naive_rmse = float(np.sqrt(mean_squared_error(y_true, naive_pred)))
        improves_naive = bool(rmse < naive_rmse)

        return ModelMetrics(
            mae=round(mae, 6),
            rmse=round(rmse, 6),
            r2=round(r2, 4),
            directional_accuracy=round(dir_acc, 4),
            naive_mae=round(naive_mae, 6),
            naive_rmse=round(naive_rmse, 6),
            improves_naive=improves_naive
        )

    async def train_model(
        self,
        symbol: str = "NIFTY",
        timeframe: str = "1m",
        horizon: int = settings.ML_DEFAULT_HORIZON,
        model_version: str = "v1.0.0"
    ) -> Tuple[ModelMetadata, str, str]:
        """
        Runs full reproducible training pipeline for symbol and timeframe.
        Returns (metadata, model_artifact_path, scaler_artifact_path).
        """
        df, feature_cols, target_col = await dataset_builder.build_dataset_async(
            symbol=symbol, timeframe=timeframe, horizon=horizon, limit=250
        )

        splits = dataset_builder.split_chronologically(
            df=df,
            feature_cols=feature_cols,
            target_col=target_col,
            train_ratio=settings.ML_TRAIN_RATIO,
            val_ratio=settings.ML_VALIDATION_RATIO,
            test_ratio=settings.ML_TEST_RATIO
        )

        X_train, y_train = splits["X_train"], splits["y_train"]
        X_val, y_val = splits["X_val"], splits["y_val"]
        X_test, y_test = splits["X_test"], splits["y_test"]

        # 1. Fit Preprocessor ONLY on Training set X_train
        preprocessor = FeaturePreprocessor(feature_list=feature_cols)
        preprocessor.fit(X_train)
        X_train_scaled = preprocessor.transform(X_train)
        X_val_scaled = preprocessor.transform(X_val)
        X_test_scaled = preprocessor.transform(X_test)

        # 2. Fit Baseline Model ONLY on Training set
        model = GradientBoostingModel()
        model.fit(X_train_scaled, y_train)

        # 3. Evaluate Metrics on Validation set
        val_preds = model.predict(X_val_scaled)
        metrics = self.evaluate_performance(y_val, val_preds)

        # 4. Save Versioned Artifacts
        model_id = str(uuid.uuid4())
        art_dir = os.path.join(settings.ML_ARTIFACT_PATH, f"{symbol.lower()}_{timeframe}_{model_version}")
        os.makedirs(art_dir, exist_ok=True)

        model_path = os.path.join(art_dir, "model.joblib")
        scaler_path = os.path.join(art_dir, "preprocessor.json")
        meta_path = os.path.join(art_dir, "metadata.json")

        model.save(model_path)
        preprocessor.save(scaler_path)

        now = datetime.datetime.now(datetime.timezone.utc)
        metadata = ModelMetadata(
            model_id=model_id,
            model_name="GradientBoostingRegressor",
            model_version=model_version,
            training_timestamp=now,
            symbol=symbol.upper(),
            timeframe=timeframe,
            target=PredictionTarget.FUTURE_RETURN,
            target_horizon=horizon,
            feature_list=feature_cols,
            training_rows=len(X_train),
            validation_rows=len(X_val),
            test_rows=len(X_test),
            metrics=metrics,
            status=ModelStatus.EXPERIMENTAL,
            data_mode="MOCK / SIMULATED DATA",
            preprocessing_version="v1"
        )

        with open(meta_path, "w") as f:
            f.write(metadata.model_dump_json(indent=2))

        logger.info(f"TRAINING COMPLETE [{symbol} {timeframe}]: Model ID={model_id}, RMSE={metrics.rmse}, Improves Naive={metrics.improves_naive}")
        return metadata, model_path, scaler_path

training_service = ModelTrainingService()
