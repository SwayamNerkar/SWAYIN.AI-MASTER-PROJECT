import math
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from app.core.config import settings

class TechnicalIndicatorEngine:
    """
    Production-Grade Technical Indicator & Feature Calculation Engine.
    Vectorized using NumPy and Pandas with STRICT ZERO LOOK-AHEAD BIAS.
    """

    def __init__(
        self,
        sma_periods: Optional[List[int]] = None,
        ema_periods: Optional[List[int]] = None,
        rsi_period: int = settings.RSI_PERIOD,
        atr_period: int = settings.ATR_PERIOD,
        adx_period: int = settings.ADX_PERIOD,
        macd_fast: int = settings.MACD_FAST,
        macd_slow: int = settings.MACD_SLOW,
        macd_signal: int = settings.MACD_SIGNAL,
        stoch_k: int = settings.STOCHASTIC_K,
        stoch_d: int = settings.STOCHASTIC_D,
        roc_period: int = settings.ROC_PERIOD
    ):
        self.sma_periods = sma_periods or settings.SMA_PERIODS
        self.ema_periods = ema_periods or settings.EMA_PERIODS
        self.rsi_period = rsi_period
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.stoch_k = stoch_k
        self.stoch_d = stoch_d
        self.roc_period = roc_period

    def calculate_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes chronological OHLCV DataFrame (ordered t_0 .. t_now) and computes all feature columns.
        Guarantees zero look-ahead bias.
        """
        if df.empty or len(df) == 0:
            return df

        res = df.copy()
        
        # Ensure numeric types
        for col in ["open", "high", "low", "close", "volume"]:
            if col in res.columns:
                res[col] = pd.to_numeric(res[col], errors="coerce")

        close = res["close"]
        open_p = res["open"]
        high = res["high"]
        low = res["low"]
        volume = res["volume"] if "volume" in res.columns else pd.Series(0, index=res.index)
        prev_close = close.shift(1)

        # ------------------------------------------------------------------
        # 1. Price Features
        # ------------------------------------------------------------------
        res["price_change_abs"] = close - prev_close
        res["price_change_pct"] = np.where(prev_close > 0, (res["price_change_abs"] / prev_close) * 100.0, 0.0)
        res["log_return"] = np.where((close > 0) & (prev_close > 0), np.log(close / prev_close), 0.0)
        
        res["candle_body"] = (close - open_p).abs()
        res["upper_wick"] = high - np.maximum(open_p, close)
        res["lower_wick"] = np.minimum(open_p, close) - low
        res["candle_range"] = high - low
        res["body_to_range_ratio"] = np.where(res["candle_range"] > 0, res["candle_body"] / res["candle_range"], 0.0)

        # ------------------------------------------------------------------
        # 2. Trend Features (SMA, EMA, VWAP, MACD, ADX)
        # ------------------------------------------------------------------
        # SMAs
        for p in self.sma_periods:
            res[f"sma_{p}"] = close.rolling(window=p, min_periods=p).mean()

        # EMAs
        for p in self.ema_periods:
            res[f"ema_{p}"] = close.ewm(span=p, adjust=False, min_periods=p).mean()

        # Intraday Cumulative VWAP
        typical_price = (high + low + close) / 3.0
        tp_vol = typical_price * volume
        res["vwap"] = tp_vol.cumsum() / volume.cumsum().replace(0, np.nan)

        # MACD
        ema_fast = close.ewm(span=self.macd_fast, adjust=False, min_periods=self.macd_fast).mean()
        ema_slow = close.ewm(span=self.macd_slow, adjust=False, min_periods=self.macd_slow).mean()
        res["macd_line"] = ema_fast - ema_slow
        res["macd_signal"] = res["macd_line"].ewm(span=self.macd_signal, adjust=False, min_periods=self.macd_signal).mean()
        res["macd_hist"] = res["macd_line"] - res["macd_signal"]

        # ADX (Average Directional Index)
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        atr_series = tr.rolling(window=self.adx_period, min_periods=self.adx_period).mean()
        plus_di = 100.0 * (pd.Series(plus_dm, index=res.index).rolling(window=self.adx_period, min_periods=self.adx_period).mean() / atr_series.replace(0, np.nan))
        minus_di = 100.0 * (pd.Series(minus_dm, index=res.index).rolling(window=self.adx_period, min_periods=self.adx_period).mean() / atr_series.replace(0, np.nan))

        dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        res["plus_di"] = plus_di
        res["minus_di"] = minus_di
        res["adx"] = dx.rolling(window=self.adx_period, min_periods=self.adx_period).mean()

        # ------------------------------------------------------------------
        # 3. Momentum Features (RSI, ROC, Stochastic)
        # ------------------------------------------------------------------
        # RSI
        delta = close.diff()
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)
        avg_gain = pd.Series(gain, index=res.index).rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        avg_loss = pd.Series(loss, index=res.index).rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        
        # When avg_loss == 0 and avg_gain > 0 -> RSI = 100; when both 0 -> RSI = 50
        rs = np.where(avg_loss == 0, np.where(avg_gain > 0, np.inf, 0.0), avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss))
        res["rsi_14"] = np.where(np.isnan(avg_gain), np.nan, np.where(np.isinf(rs), 100.0, 100.0 - (100.0 / (1.0 + rs))))

        # ROC
        past_close = close.shift(self.roc_period)
        res["roc_12"] = np.where(past_close > 0, ((close - past_close) / past_close) * 100.0, 0.0)

        # Stochastic Oscillator (%K, %D)
        lowest_low = low.rolling(window=self.stoch_k, min_periods=self.stoch_k).min()
        highest_high = high.rolling(window=self.stoch_k, min_periods=self.stoch_k).max()
        res["stoch_k"] = np.where((highest_high - lowest_low) > 0, ((close - lowest_low) / (highest_high - lowest_low)) * 100.0, 50.0)
        res["stoch_d"] = res["stoch_k"].rolling(window=self.stoch_d, min_periods=self.stoch_d).mean()

        # ------------------------------------------------------------------
        # 4. Volatility Features (ATR, Rolling Std, Realized Volatility)
        # ------------------------------------------------------------------
        res["atr_14"] = atr_series
        res["normalized_atr"] = np.where(close > 0, (res["atr_14"] / close) * 100.0, 0.0)
        res["rolling_std_20"] = close.rolling(window=20, min_periods=20).std()
        res["realized_volatility"] = res["rolling_std_20"] * math.sqrt(252)
        res["high_low_range_pct"] = np.where(close > 0, ((high - low) / close) * 100.0, 0.0)
        res["volatility_change"] = res["atr_14"] - res["atr_14"].shift(1)

        # ------------------------------------------------------------------
        # 5. Volume Features
        # ------------------------------------------------------------------
        res["volume_ma_20"] = volume.rolling(window=20, min_periods=20).mean()
        res["relative_volume"] = np.where(res["volume_ma_20"] > 0, volume / res["volume_ma_20"], 1.0)
        res["volume_change"] = volume - volume.shift(1)
        res["volume_ratio"] = np.where(volume.shift(1) > 0, volume / volume.shift(1), 1.0)

        # ------------------------------------------------------------------
        # 6. Price-Action Features
        # ------------------------------------------------------------------
        res["candle_direction"] = np.where(close > open_p, 1.0, np.where(close < open_p, -1.0, 0.0))
        res["body_pct"] = res["body_to_range_ratio"] * 100.0
        res["upper_wick_ratio"] = np.where(res["candle_range"] > 0, res["upper_wick"] / res["candle_range"], 0.0)
        res["lower_wick_ratio"] = np.where(res["candle_range"] > 0, res["lower_wick"] / res["candle_range"], 0.0)

        rolling_high_20 = high.rolling(window=20, min_periods=20).max()
        rolling_low_20 = low.rolling(window=20, min_periods=20).min()
        res["rolling_high_20"] = rolling_high_20
        res["rolling_low_20"] = rolling_low_20

        res["dist_from_rolling_high_pct"] = np.where(close > 0, ((rolling_high_20 - close) / close) * 100.0, 0.0)
        res["dist_from_rolling_low_pct"] = np.where(close > 0, ((close - rolling_low_20) / close) * 100.0, 0.0)
        res["breakout_distance_pct"] = np.where(rolling_high_20 > 0, ((close - rolling_high_20) / rolling_high_20) * 100.0, 0.0)

        return res

indicator_engine = TechnicalIndicatorEngine()
