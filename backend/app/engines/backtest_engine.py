import uuid
import logging
import datetime
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from app.core.config import settings
from app.interfaces.backtest import BacktestEngineInterface
from app.schemas.backtest import (
    BacktestConfig, BacktestResult, BacktestPredictionRecord,
    GroupedMetrics, ErrorAnalysisSummary, WalkForwardMode
)
from app.ml_pipeline.dataset_builder import dataset_builder
from app.ml_pipeline.preprocessing import FeaturePreprocessor
from app.ml_pipeline.baseline_model import GradientBoostingModel

logger = logging.getLogger("swayin")

# Code maps to string labels for regime grouping
CODE_TO_REGIME = {1.0: "TRENDING_UP", -1.0: "TRENDING_DOWN", 0.0: "SIDEWAYS", 0.5: "HIGH_VOLATILITY", 2.0: "REVERSAL"}
CODE_TO_VOL = {0.0: "LOW", 1.0: "MEDIUM", 2.0: "HIGH"}

class WalkForwardBacktestEngine(BacktestEngineInterface):
    """
    Production Walk-Forward Backtest & Prediction Evaluation Engine.
    Executes expanding-window model training and evaluation with zero future data leakage.
    Produces comprehensive statistical, regime-wise, and volatility-wise reports.
    """

    def _get_direction_label(self, val: float, threshold: float = 0.0002) -> str:
        if val > threshold:
            return "UP"
        elif val < -threshold:
            return "DOWN"
        return "FLAT"

    def _calculate_group_metrics(self, group_records: List[BacktestPredictionRecord]) -> GroupedMetrics:
        if not group_records:
            return GroupedMetrics(sample_count=0, mae=0.0, rmse=0.0, directional_accuracy=0.0, mean_error=0.0)
        
        y_true = np.array([r.actual for r in group_records])
        y_pred = np.array([r.prediction for r in group_records])
        
        mae = float(mean_absolute_error(y_true, y_pred))
        rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
        mean_err = float(np.mean(y_true - y_pred))
        dir_acc = float(np.mean([r.direction_correct for r in group_records]))

        return GroupedMetrics(
            sample_count=len(group_records),
            mae=round(mae, 6),
            rmse=round(rmse, 6),
            directional_accuracy=round(dir_acc, 4),
            mean_error=round(mean_err, 6)
        )

    def run_backtest_on_candles(self, candles: list, config: BacktestConfig) -> BacktestResult:
        if not candles or len(candles) < config.initial_train_bars + config.eval_window_bars:
            raise ValueError(f"Insufficient historical candles ({len(candles) if candles else 0}) for backtest (need >= {config.initial_train_bars + config.eval_window_bars}).")

        # 1. Build timestamp-aligned dataset
        df, feature_cols, target_col = dataset_builder.build_dataset_from_candles(
            candles, timeframe=config.timeframe, horizon=config.horizon_bars
        )

        n = len(df)
        initial_train = config.initial_train_bars
        eval_window = config.eval_window_bars

        if n <= initial_train:
            raise ValueError(f"Dataset rows ({n}) after feature calculation <= initial_train_bars ({initial_train}).")

        records: List[BacktestPredictionRecord] = []
        model_id = f"gb_regressor_{config.horizon_bars}b"
        
        # 2. Walk-Forward Expanding-Window Training & Evaluation Loop
        curr_idx = initial_train
        step = 0

        while curr_idx < n:
            eval_end = min(curr_idx + eval_window, n)
            
            # Define expanding train slice and evaluation slice
            train_df = df.iloc[:curr_idx]
            eval_df = df.iloc[curr_idx:eval_end]

            X_train = train_df[feature_cols].copy()
            y_train = train_df[target_col].copy()
            X_eval = eval_df[feature_cols].copy()
            y_eval = eval_df[target_col].copy()

            # CRITICAL LEAKAGE SAFETY: Scaler fitted STRICTLY ONLY on Train Slice!
            preprocessor = FeaturePreprocessor(feature_list=feature_cols)
            preprocessor.fit(X_train)
            X_train_scaled = preprocessor.transform(X_train)
            X_eval_scaled = preprocessor.transform(X_eval)

            # Model trained STRICTLY ONLY on Train Slice!
            model = GradientBoostingModel(n_estimators=50, random_state=settings.ML_RANDOM_SEED)
            model.fit(X_train_scaled, y_train)

            eval_preds = model.predict(X_eval_scaled)

            # Record individual evaluation prediction results
            for idx_local, (idx_global, eval_row) in enumerate(eval_df.iterrows()):
                pred_val = float(eval_preds[idx_local])
                act_val = float(eval_row[target_col])
                err = act_val - pred_val
                abs_err = abs(err)
                sq_err = err ** 2

                pred_dir = self._get_direction_label(pred_val)
                act_dir = self._get_direction_label(act_val)
                dir_correct = bool(np.sign(act_val) == np.sign(pred_val))

                reg_code = eval_row.get("regime_code", 0.0)
                vol_code = eval_row.get("volatility_code", 1.0)
                reg_name = CODE_TO_REGIME.get(reg_code, "SIDEWAYS")
                vol_name = CODE_TO_VOL.get(vol_code, "MEDIUM")

                rec = BacktestPredictionRecord(
                    timestamp=eval_row["timestamp"],
                    symbol=config.symbol.upper(),
                    timeframe=config.timeframe,
                    model_id=model_id,
                    model_version=config.model_version,
                    prediction=round(pred_val, 6),
                    actual=round(act_val, 6),
                    prediction_error=round(err, 6),
                    absolute_error=round(abs_err, 6),
                    squared_error=round(sq_err, 8),
                    predicted_direction=pred_dir,
                    actual_direction=act_dir,
                    direction_correct=dir_correct,
                    horizon_bars=config.horizon_bars,
                    directional_regime=reg_name,
                    volatility_state=vol_name,
                    regime_confidence=round(float(eval_row.get("regime_confidence", 0.5)), 2),
                    data_mode="MOCK / SIMULATED DATA",
                    provider="mock"
                )
                records.append(rec)

            curr_idx = eval_end
            step += 1

        # 3. Overall Statistical & Directional Metrics
        y_true_all = np.array([r.actual for r in records])
        y_pred_all = np.array([r.prediction for r in records])

        overall_mae = float(mean_absolute_error(y_true_all, y_pred_all))
        overall_rmse = float(np.sqrt(mean_squared_error(y_true_all, y_pred_all)))
        overall_r2 = float(r2_score(y_true_all, y_pred_all)) if len(y_true_all) > 2 else 0.0
        overall_dir_acc = float(np.mean([r.direction_correct for r in records]))

        overall_metrics = {
            "mae": round(overall_mae, 6),
            "rmse": round(overall_rmse, 6),
            "r2": round(overall_r2, 4),
            "directional_accuracy": round(overall_dir_acc, 4)
        }

        # 4. Naive Zero-Return Baseline Comparison
        naive_preds = np.zeros_like(y_true_all)
        naive_mae = float(mean_absolute_error(y_true_all, naive_preds))
        naive_rmse = float(np.sqrt(mean_squared_error(y_true_all, naive_preds)))
        naive_r2 = float(r2_score(y_true_all, naive_preds)) if len(y_true_all) > 2 else 0.0
        naive_dir_acc = 0.50

        naive_metrics = {
            "mae": round(naive_mae, 6),
            "rmse": round(naive_rmse, 6),
            "r2": round(naive_r2, 4),
            "directional_accuracy": round(naive_dir_acc, 4)
        }

        improves_naive = bool(overall_rmse < naive_rmse)

        # 5. Task 1.4 Regime-Wise & Volatility-Wise Analysis
        regime_groups = {}
        for r_name in ["TRENDING_UP", "TRENDING_DOWN", "SIDEWAYS", "HIGH_VOLATILITY", "REVERSAL"]:
            sub_recs = [r for r in records if r.directional_regime == r_name]
            regime_groups[r_name] = self._calculate_group_metrics(sub_recs)

        vol_groups = {}
        for v_name in ["LOW", "MEDIUM", "HIGH"]:
            sub_recs = [r for r in records if r.volatility_state == v_name]
            vol_groups[v_name] = self._calculate_group_metrics(sub_recs)

        # 6. Error & Residual Analysis Summary
        errors = np.array([r.prediction_error for r in records])
        abs_errors = np.array([r.absolute_error for r in records])
        mean_pred = float(np.mean(y_pred_all))
        mean_act = float(np.mean(y_true_all))
        bias = round(mean_pred - mean_act, 6)
        med_abs_err = float(np.median(abs_errors))
        max_abs_err = float(np.max(abs_errors))

        # Consecutive errors calculation
        max_consec = 0
        curr_consec = 0
        for r in records:
            if not r.direction_correct:
                curr_consec += 1
                max_consec = max(max_consec, curr_consec)
            else:
                curr_consec = 0

        error_summary = ErrorAnalysisSummary(
            mean_prediction=round(mean_pred, 6),
            mean_actual=round(mean_act, 6),
            prediction_bias=bias,
            median_abs_error=round(med_abs_err, 6),
            max_abs_error=round(max_abs_err, 6),
            consecutive_errors_max=max_consec
        )

        backtest_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc)

        return BacktestResult(
            backtest_id=backtest_id,
            config=config,
            created_at=now,
            total_candles=len(candles),
            prediction_count=len(records),
            skipped_count=len(candles) - len(df),
            warmup_rows_skipped=30,
            overall_metrics=overall_metrics,
            naive_metrics=naive_metrics,
            improves_naive=improves_naive,
            regime_metrics=regime_groups,
            volatility_metrics=vol_groups,
            error_analysis=error_summary,
            predictions=records,
            data_mode="MOCK / SIMULATED DATA",
            provider="mock",
            status="COMPLETED"
        )

backtest_engine = WalkForwardBacktestEngine()
