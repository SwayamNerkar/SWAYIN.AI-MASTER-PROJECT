import os
import json
import logging
import datetime
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from app.core.config import settings
from app.interfaces.ml import PredictionServiceInterface
from app.schemas.ml import PredictionResponse, ModelMetadata, ModelStatus
from app.services.market_data_service import market_data_service
from app.services.feature_service import feature_service
from app.engines.regime_engine import regime_engine
from app.ml_pipeline.preprocessing import FeaturePreprocessor
from app.ml_pipeline.baseline_model import GradientBoostingModel
from app.ml_pipeline.dataset_builder import REGIME_MAP, VOL_STATE_MAP

logger = logging.getLogger("swayin")

class PredictionService(PredictionServiceInterface):
    """
    Production Inference Service.
    Loads versioned model and fitted preprocessor artifacts, validates schema,
    and returns strongly typed prediction responses.
    """

    async def predict_latest(self, symbol: str, timeframe: str = "1m") -> PredictionResponse:
        sym = symbol.upper()
        art_dir = os.path.join(settings.ML_ARTIFACT_PATH, f"{sym.lower()}_{timeframe}_v1.0.0")
        model_path = os.path.join(art_dir, "model.joblib")
        scaler_path = os.path.join(art_dir, "preprocessor.json")
        meta_path = os.path.join(art_dir, "metadata.json")

        if not os.path.exists(model_path) or not os.path.exists(scaler_path):
            from app.ml_pipeline.training_service import training_service
            meta, model_path, scaler_path = await training_service.train_model(symbol=sym, timeframe=timeframe)
        else:
            with open(meta_path, "r") as f:
                meta = ModelMetadata.model_validate_json(f.read())

        preprocessor = FeaturePreprocessor().load(scaler_path)
        model = GradientBoostingModel()
        model.load(model_path)

        candles = await market_data_service.get_ohlcv(sym, timeframe=timeframe, limit=50)
        snapshots = feature_service.generate_feature_series(candles, timeframe=timeframe)
        regimes = regime_engine.classify_regime_series(snapshots)
        latest_snap = snapshots[-1]
        latest_reg = regimes[-1]

        feat_dict = dict(latest_snap.features)
        feat_dict["regime_code"] = REGIME_MAP.get(latest_reg.directional_regime.value, 0.0)
        feat_dict["volatility_code"] = VOL_STATE_MAP.get(latest_reg.volatility_state.value, 1.0)
        feat_dict["regime_confidence"] = latest_reg.confidence

        inf_df = pd.DataFrame([feat_dict])
        inf_scaled = preprocessor.transform(inf_df)
        pred_val = float(model.predict(inf_scaled)[0])

        direction = "FLAT"
        if pred_val > 0.0002:
            direction = "UP"
        elif pred_val < -0.0002:
            direction = "DOWN"

        return PredictionResponse(
            symbol=sym,
            timestamp=latest_snap.timestamp,
            timeframe=timeframe,
            model_id=meta.model_id,
            model_version=meta.model_version,
            prediction_target=meta.target.value,
            horizon_bars=meta.target_horizon,
            predicted_value=round(pred_val, 6),
            predicted_direction=direction,
            data_mode="MOCK / SIMULATED DATA",
            model_status=meta.status
        )

prediction_service = PredictionService()
