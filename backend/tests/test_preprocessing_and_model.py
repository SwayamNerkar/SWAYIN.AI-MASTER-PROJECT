import os
import tempfile
import pytest
import pandas as pd
import numpy as np
from app.ml_pipeline.preprocessing import FeaturePreprocessor
from app.ml_pipeline.baseline_model import GradientBoostingModel

def test_preprocessor_fitting_and_transformation():
    # Synthetic data
    X_train = pd.DataFrame({"f1": [1.0, 2.0, 3.0, 4.0], "f2": [10.0, 20.0, 30.0, 40.0]})
    X_test = pd.DataFrame({"f1": [5.0, 6.0], "f2": [50.0, 60.0]})
    
    preprocessor = FeaturePreprocessor(feature_list=["f1", "f2"])
    # 1. Scaler MUST be fitted strictly on X_train
    preprocessor.fit(X_train)
    assert preprocessor.is_fitted is True
    
    # 2. Transform X_train & X_test
    X_train_scaled = preprocessor.transform(X_train)
    X_test_scaled = preprocessor.transform(X_test)
    
    assert X_train_scaled.shape == (4, 2)
    assert X_test_scaled.shape == (2, 2)
    
    # 3. Serialization test
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "preprocessor.json")
        preprocessor.save(path)
        
        loaded = FeaturePreprocessor().load(path)
        assert loaded.is_fitted is True
        assert loaded.feature_list == ["f1", "f2"]

def test_baseline_model_fit_predict_save_load():
    X = pd.DataFrame({"f1": np.random.randn(50), "f2": np.random.randn(50)})
    y = pd.Series(0.5 * X["f1"] - 0.2 * X["f2"] + np.random.randn(50) * 0.01)
    
    model = GradientBoostingModel(n_estimators=20, random_state=42)
    model.fit(X, y)
    assert model.is_fitted is True
    
    preds = model.predict(X)
    assert len(preds) == 50
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "model.joblib")
        model.save(path)
        
        loaded_model = GradientBoostingModel()
        loaded_model.load(path)
        assert loaded_model.is_fitted is True
        loaded_preds = loaded_model.predict(X)
        np.testing.assert_array_almost_equal(preds, loaded_preds)
