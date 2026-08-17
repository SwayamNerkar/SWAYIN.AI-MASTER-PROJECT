import pytest
from app.ml_pipeline.dataset_builder import dataset_builder
from test_dataset_builder import generate_mock_candles

def test_ml_feature_matrix_leakage_protection():
    """
    CRITICAL ML LEAKAGE PROTECTION TEST:
    Feature matrix feature_cols MUST NOT contain any future price, return, or regime columns.
    """
    candles = generate_mock_candles(100)
    df, feature_cols, target_col = dataset_builder.build_dataset_from_candles(candles, horizon=3)
    
    # 1. Target column must not be in feature set
    assert target_col not in feature_cols
    
    # 2. Raw future columns must not be in feature set
    forbidden = ["future_close", "future_high", "future_low", "future_volume", "future_regime"]
    for col in forbidden:
        assert col not in feature_cols

def test_future_candle_modification_dataset_leakage_protection():
    """
    Modifying a future candle (index 80) MUST NOT alter the feature vector at index 40!
    """
    candles_orig = generate_mock_candles(100)
    df_orig, feature_cols, _ = dataset_builder.build_dataset_from_candles(candles_orig, horizon=3)
    row_40_orig = df_orig.iloc[40][feature_cols].to_dict()
    
    # Alter candle 80
    candles_mod = generate_mock_candles(100)
    candles_mod[80].close = 99999.0
    candles_mod[80].high = 99999.0
    df_mod, _, _ = dataset_builder.build_dataset_from_candles(candles_mod, horizon=3)
    row_40_mod = df_mod.iloc[40][feature_cols].to_dict()
    
    for k in feature_cols:
        assert row_40_orig[k] == pytest.approx(row_40_mod[k]), f"Feature leakage detected on column {k}!"
