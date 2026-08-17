import datetime
import pytest
import numpy as np
import pytz
from app.schemas.market_data import OHLCVCandle
from app.ml_pipeline.dataset_builder import dataset_builder

IST = pytz.timezone("Asia/Kolkata")

def generate_mock_candles(count: int = 100) -> list[OHLCVCandle]:
    base_time = datetime.datetime(2026, 8, 17, 9, 15, tzinfo=IST)
    candles = []
    np.random.seed(42)
    c = 24500.0
    for i in range(count):
        t = base_time + datetime.timedelta(minutes=i)
        c += np.random.uniform(-3, 4)
        o = c - np.random.uniform(-1, 1)
        h = max(o, c) + np.random.uniform(0, 2)
        l = min(o, c) - np.random.uniform(0, 2)
        v = int(np.random.uniform(10000, 50000))
        candles.append(OHLCVCandle(
            symbol="NIFTY",
            timestamp=t,
            interval="1m",
            open=round(o, 2),
            high=round(h, 2),
            low=round(l, 2),
            close=round(c, 2),
            volume=v
        ))
    return candles

def test_dataset_builder_target_and_features():
    candles = generate_mock_candles(100)
    df, feature_cols, target_col = dataset_builder.build_dataset_from_candles(candles, horizon=3)
    
    assert target_col == "future_return"
    assert "close" not in feature_cols
    assert "timestamp" not in feature_cols
    assert target_col not in feature_cols
    assert len(df) > 0
    assert "future_return" in df.columns

def test_chronological_train_val_test_split():
    candles = generate_mock_candles(100)
    df, feature_cols, target_col = dataset_builder.build_dataset_from_candles(candles, horizon=3)
    
    splits = dataset_builder.split_chronologically(df, feature_cols, target_col, 0.70, 0.15, 0.15)
    
    train_ts = splits["train_ts"]
    val_ts = splits["val_ts"]
    test_ts = splits["test_ts"]
    
    # Verify strict temporal ordering: train_ts < val_ts < test_ts
    assert max(train_ts) < min(val_ts), "Train timestamps overlap with Validation timestamps!"
    assert max(val_ts) < min(test_ts), "Validation timestamps overlap with Test timestamps!"
