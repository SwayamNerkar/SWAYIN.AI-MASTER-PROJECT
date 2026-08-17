import pytest
import pandas as pd
import numpy as np
from app.ml_pipeline.training_service import ModelTrainingService

def test_model_evaluation_metrics_and_naive_baseline():
    y_true = pd.Series([0.002, -0.001, 0.003, -0.002, 0.001])
    # Accurate predictions with slight noise
    y_pred = np.array([0.0018, -0.0012, 0.0028, -0.0019, 0.0009])
    
    metrics = ModelTrainingService.evaluate_performance(y_true, y_pred)
    
    assert metrics.mae > 0.0
    assert metrics.rmse > 0.0
    assert metrics.directional_accuracy == 1.0  # 100% directional match
    assert metrics.naive_rmse > metrics.rmse    # Model should beat zero-return naive baseline
    assert metrics.improves_naive is True
