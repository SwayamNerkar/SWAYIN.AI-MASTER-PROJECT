import math
import logging
import datetime
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
import pytz

from app.core.config import settings
from app.interfaces.feature_engine import FeatureEngineeringInterface
from app.schemas.market_data import OHLCVCandle
from app.schemas.features import (
    FeatureSnapshot, FeatureMetadata, FeatureCategory, FeatureSeriesResponse
)
from app.engines.indicator_engine import TechnicalIndicatorEngine, indicator_engine

logger = logging.getLogger("swayin")

class FeatureEngineeringService(FeatureEngineeringInterface):
    """
    Production Feature Engineering Subsystem Service.
    Transforms validated OHLCV candles into clean, timestamp-aligned numerical features.
    Guarantees strict zero look-ahead bias and tracks warmup readiness.
    """

    IST = pytz.timezone("Asia/Kolkata")
    WARMUP_BARS_REQUIRED = 30  # Minimum bars required for stable technical indicators

    def __init__(self, engine: Optional[TechnicalIndicatorEngine] = None):
        self.engine = engine or indicator_engine
        self._metadata_registry = self._build_metadata_registry()

    def _build_metadata_registry(self) -> List[FeatureMetadata]:
        """Builds a complete registry of metadata for all supported features."""
        meta = [
            # Price Features
            FeatureMetadata(feature_name="price_change_abs", category=FeatureCategory.PRICE, description="Absolute price change from previous candle"),
            FeatureMetadata(feature_name="price_change_pct", category=FeatureCategory.PRICE, description="Percentage price change from previous candle"),
            FeatureMetadata(feature_name="log_return", category=FeatureCategory.PRICE, description="Logarithmic price return"),
            FeatureMetadata(feature_name="candle_body", category=FeatureCategory.PRICE, description="Absolute candle body range (abs(close - open))"),
            FeatureMetadata(feature_name="upper_wick", category=FeatureCategory.PRICE, description="Upper wick height (high - max(open, close))"),
            FeatureMetadata(feature_name="lower_wick", category=FeatureCategory.PRICE, description="Lower wick height (min(open, close) - low)"),
            FeatureMetadata(feature_name="candle_range", category=FeatureCategory.PRICE, description="Total candle range (high - low)"),
            FeatureMetadata(feature_name="body_to_range_ratio", category=FeatureCategory.PRICE, description="Ratio of candle body to total range"),
            
            # Trend Indicators
            FeatureMetadata(feature_name="sma_10", category=FeatureCategory.TREND, period=10, description="10-period Simple Moving Average"),
            FeatureMetadata(feature_name="sma_20", category=FeatureCategory.TREND, period=20, description="20-period Simple Moving Average"),
            FeatureMetadata(feature_name="sma_50", category=FeatureCategory.TREND, period=50, description="50-period Simple Moving Average"),
            FeatureMetadata(feature_name="ema_9", category=FeatureCategory.TREND, period=9, description="9-period Exponential Moving Average"),
            FeatureMetadata(feature_name="ema_21", category=FeatureCategory.TREND, period=21, description="21-period Exponential Moving Average"),
            FeatureMetadata(feature_name="ema_50", category=FeatureCategory.TREND, period=50, description="50-period Exponential Moving Average"),
            FeatureMetadata(feature_name="vwap", category=FeatureCategory.TREND, description="Volume Weighted Average Price", requires_volume=True),
            FeatureMetadata(feature_name="macd_line", category=FeatureCategory.TREND, period=12, description="MACD line (EMA 12 - EMA 26)"),
            FeatureMetadata(feature_name="macd_signal", category=FeatureCategory.TREND, period=9, description="MACD signal line (EMA 9 of MACD line)"),
            FeatureMetadata(feature_name="macd_hist", category=FeatureCategory.TREND, description="MACD histogram (MACD line - Signal line)"),
            FeatureMetadata(feature_name="adx", category=FeatureCategory.TREND, period=14, description="Average Directional Index (14 period)"),
            
            # Momentum Indicators
            FeatureMetadata(feature_name="rsi_14", category=FeatureCategory.MOMENTUM, period=14, description="14-period Relative Strength Index"),
            FeatureMetadata(feature_name="roc_12", category=FeatureCategory.MOMENTUM, period=12, description="12-period Rate of Change percentage"),
            FeatureMetadata(feature_name="stoch_k", category=FeatureCategory.MOMENTUM, period=14, description="Stochastic Oscillator %K line"),
            FeatureMetadata(feature_name="stoch_d", category=FeatureCategory.MOMENTUM, period=3, description="Stochastic Oscillator %D signal line"),
            
            # Volatility Indicators
            FeatureMetadata(feature_name="atr_14", category=FeatureCategory.VOLATILITY, period=14, description="14-period Average True Range"),
            FeatureMetadata(feature_name="normalized_atr", category=FeatureCategory.VOLATILITY, period=14, description="Normalized ATR percentage (ATR / Close * 100)"),
            FeatureMetadata(feature_name="rolling_std_20", category=FeatureCategory.VOLATILITY, period=20, description="20-period rolling close standard deviation"),
            FeatureMetadata(feature_name="realized_volatility", category=FeatureCategory.VOLATILITY, period=20, description="Annualized realized volatility"),
            FeatureMetadata(feature_name="high_low_range_pct", category=FeatureCategory.VOLATILITY, description="High-Low range as percentage of close"),
            
            # Volume Features
            FeatureMetadata(feature_name="volume_ma_20", category=FeatureCategory.VOLUME, period=20, description="20-period Simple Moving Average of Volume", requires_volume=True),
            FeatureMetadata(feature_name="relative_volume", category=FeatureCategory.VOLUME, period=20, description="Relative Volume ratio (Volume / Volume MA 20)", requires_volume=True),
            FeatureMetadata(feature_name="volume_change", category=FeatureCategory.VOLUME, description="Volume change from previous candle", requires_volume=True),
            
            # Price-Action Features
            FeatureMetadata(feature_name="candle_direction", category=FeatureCategory.PRICE_ACTION, description="Candle direction (+1 bullish, -1 bearish, 0 neutral)"),
            FeatureMetadata(feature_name="dist_from_rolling_high_pct", category=FeatureCategory.PRICE_ACTION, period=20, description="Percentage distance from 20-bar rolling high"),
            FeatureMetadata(feature_name="dist_from_rolling_low_pct", category=FeatureCategory.PRICE_ACTION, period=20, description="Percentage distance from 20-bar rolling low"),
            FeatureMetadata(feature_name="breakout_distance_pct", category=FeatureCategory.PRICE_ACTION, period=20, description="Breakout distance percentage relative to rolling high")
        ]
        return meta

    def get_feature_metadata(self) -> List[FeatureMetadata]:
        return self._metadata_registry

    def _candles_to_dataframe(self, candles: List[OHLCVCandle]) -> pd.DataFrame:
        """Converts typed candle list into Pandas DataFrame ordered by timestamp."""
        rows = []
        for c in candles:
            rows.append({
                "timestamp": c.timestamp,
                "symbol": c.symbol,
                "interval": c.interval,
                "open": c.open,
                "high": c.high,
                "low": c.low,
                "close": c.close,
                "volume": c.volume
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def generate_feature_series(self, candles: List[OHLCVCandle], timeframe: str = "1m") -> List[FeatureSnapshot]:
        """
        Generates historical feature snapshot series for every bar in candles.
        Guarantees ZERO look-ahead bias by calculating strictly on chronological slice [0..i].
        """
        if not candles:
            return []

        symbol = candles[0].symbol
        df = self._candles_to_dataframe(candles)
        df_feat = self.engine.calculate_all_features(df)

        snapshots = []
        feature_names = [m.feature_name for m in self._metadata_registry]

        for i in range(len(df_feat)):
            row = df_feat.iloc[i]
            ts = row["timestamp"]
            if isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
            if ts.tzinfo is None:
                ts = self.IST.localize(ts)
            else:
                ts = ts.astimezone(self.IST)

            feat_dict = {}
            validity_dict = {}

            # i+1 is bars available so far
            warmup_ready = (i + 1 >= self.WARMUP_BARS_REQUIRED)

            for fname in feature_names:
                val = row.get(fname)
                if val is None or pd.isna(val) or np.isinf(val):
                    feat_dict[fname] = None
                    validity_dict[fname] = False
                else:
                    feat_dict[fname] = round(float(val), 4)
                    validity_dict[fname] = True

            snapshot = FeatureSnapshot(
                timestamp=ts,
                symbol=symbol,
                timeframe=timeframe,
                features=feat_dict,
                feature_validity=validity_dict,
                is_snapshot_valid=self.validate_features_dict(feat_dict, validity_dict),
                warmup_ready=warmup_ready,
                data_mode="MOCK / SIMULATED DATA",
                provider="mock"
            )
            snapshots.append(snapshot)

        return snapshots

    def generate_features(self, candles: List[OHLCVCandle], timeframe: str = "1m") -> FeatureSnapshot:
        """
        Generates feature snapshot for the single latest candle in the series.
        """
        series = self.generate_feature_series(candles, timeframe=timeframe)
        if not series:
            now = datetime.datetime.now(self.IST)
            return FeatureSnapshot(
                timestamp=now,
                symbol=candles[0].symbol if candles else "NIFTY",
                timeframe=timeframe,
                features={},
                feature_validity={},
                is_snapshot_valid=False,
                warmup_ready=False,
                data_mode="MOCK / SIMULATED DATA",
                provider="mock"
            )
        return series[-1]

    def validate_features_dict(self, features: Dict[str, Optional[float]], validity: Dict[str, bool]) -> bool:
        """Checks if core price and trend features are valid (non-NaN, non-Inf)."""
        core_features = ["price_change_pct", "rsi_14", "atr_14", "macd_line"]
        for f in core_features:
            if f in features and (features[f] is None or not validity.get(f, False)):
                return False
        return True

    def validate_features(self, snapshot: FeatureSnapshot) -> bool:
        """Validates feature snapshot integrity."""
        return snapshot.is_snapshot_valid and snapshot.warmup_ready

feature_service = FeatureEngineeringService()
