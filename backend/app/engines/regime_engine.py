import math
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.interfaces.regime_engine import MarketRegimeInterface
from app.schemas.features import FeatureSnapshot
from app.schemas.regime import (
    MarketRegimeSnapshot, DirectionalRegime, VolatilityState
)
from app.engines.volatility_state_machine import VolatilityStateMachine, volatility_state_machine

logger = logging.getLogger("swayin")

class MarketRegimeEngine(MarketRegimeInterface):
    """
    Production Market Regime Classification Engine.
    Evaluates TRENDING_UP, TRENDING_DOWN, SIDEWAYS, HIGH_VOLATILITY, and REVERSAL.
    Computes explainable evidence scores, confidence, and machine-readable reason codes.
    """

    def __init__(
        self,
        vol_machine: Optional[VolatilityStateMachine] = None,
        adx_threshold: float = settings.REGIME_ADX_THRESHOLD,
        trend_score_threshold: float = settings.REGIME_TREND_SCORE_THRESHOLD,
        reversal_threshold: float = settings.REGIME_REVERSAL_THRESHOLD,
        min_confirmation_bars: int = settings.REGIME_MIN_CONFIRMATION_BARS
    ):
        self.vol_machine = vol_machine or volatility_state_machine
        self.adx_threshold = adx_threshold
        self.trend_score_threshold = trend_score_threshold
        self.reversal_threshold = reversal_threshold
        self.min_confirmation_bars = min_confirmation_bars

    def get_volatility_state(self, feature_snapshot: FeatureSnapshot) -> VolatilityState:
        vol_state, _ = self.vol_machine.evaluate_state(feature_snapshot)
        return vol_state

    def _evaluate_evidence(self, feats: Dict[str, Optional[float]]) -> Tuple[float, float, List[str]]:
        """
        Evaluates feature snapshot to compute Bullish Score, Bearish Score, and Reason Codes.
        """
        bullish_score = 0.0
        bearish_score = 0.0
        reasons = []

        ema9 = feats.get("ema_9")
        ema21 = feats.get("ema_21")
        ema50 = feats.get("ema_50")
        plus_di = feats.get("plus_di")
        minus_di = feats.get("minus_di")
        adx = feats.get("adx", 0.0)
        rsi = feats.get("rsi_14")
        macd_hist = feats.get("macd_hist")

        # 1. Moving Average Alignment (0.50 max score)
        if ema9 is not None and ema21 is not None:
            if ema9 > ema21:
                bullish_score += 0.25
                reasons.append("EMA_9_ABOVE_EMA_21")
            elif ema9 < ema21:
                bearish_score += 0.25
                reasons.append("EMA_9_BELOW_EMA_21")

        if ema21 is not None and ema50 is not None:
            if ema21 > ema50:
                bullish_score += 0.25
                reasons.append("EMA_21_ABOVE_EMA_50")
            elif ema21 < ema50:
                bearish_score += 0.25
                reasons.append("EMA_21_BELOW_EMA_50")

        # 2. Directional Indicators (0.20 max score)
        if plus_di is not None and minus_di is not None:
            if plus_di > minus_di:
                bullish_score += 0.20
                reasons.append("PLUS_DI_ABOVE_MINUS_DI")
            elif minus_di > plus_di:
                bearish_score += 0.20
                reasons.append("MINUS_DI_ABOVE_PLUS_DI")

        # 3. Momentum RSI & MACD (0.30 max score)
        if rsi is not None:
            if rsi > 52.0:
                bullish_score += 0.15
                reasons.append("RSI_BULLISH_MOMENTUM")
            elif rsi < 48.0:
                bearish_score += 0.15
                reasons.append("RSI_BEARISH_MOMENTUM")

        if macd_hist is not None:
            if macd_hist > 0:
                bullish_score += 0.15
                reasons.append("MACD_HIST_POSITIVE")
            elif macd_hist < 0:
                bearish_score += 0.15
                reasons.append("MACD_HIST_NEGATIVE")

        if adx is not None and adx >= self.adx_threshold:
            reasons.append("ADX_TREND_STRONG")

        return round(bullish_score, 2), round(bearish_score, 2), reasons

    def classify_regime(self, feature_snapshot: FeatureSnapshot) -> MarketRegimeSnapshot:
        """Classifies a single snapshot without historical stability tracking."""
        return self.classify_regime_series([feature_snapshot])[-1]

    def classify_regime_series(self, feature_snapshots: List[FeatureSnapshot]) -> List[MarketRegimeSnapshot]:
        """
        Classifies chronological series of feature snapshots with regime stability & hysteresis.
        """
        if not feature_snapshots:
            return []

        results = []
        prev_regime: Optional[DirectionalRegime] = None
        pending_regime: Optional[DirectionalRegime] = None
        confirmation_count = 0

        for snap in feature_snapshots:
            vol_state = self.get_volatility_state(snap)
            feats = snap.features
            adx = feats.get("adx", 0.0) or 0.0

            bull_score, bear_score, reasons = self._evaluate_evidence(feats)

            # Determine candidate raw regime
            candidate = DirectionalRegime.SIDEWAYS
            confidence = 0.50

            if vol_state == VolatilityState.HIGH and adx < self.adx_threshold:
                candidate = DirectionalRegime.HIGH_VOLATILITY
                confidence = 0.75
                reasons.append("HIGH_VOLATILITY_EXPANSION")

            elif bull_score >= self.trend_score_threshold and adx >= self.adx_threshold:
                if prev_regime == DirectionalRegime.TRENDING_DOWN and bull_score >= self.reversal_threshold:
                    candidate = DirectionalRegime.REVERSAL
                    confidence = round(bull_score, 2)
                    reasons.append("BULLISH_REVERSAL_CONFIRMED")
                else:
                    candidate = DirectionalRegime.TRENDING_UP
                    confidence = round(bull_score, 2)

            elif bear_score >= self.trend_score_threshold and adx >= self.adx_threshold:
                if prev_regime == DirectionalRegime.TRENDING_UP and bear_score >= self.reversal_threshold:
                    candidate = DirectionalRegime.REVERSAL
                    confidence = round(bear_score, 2)
                    reasons.append("BEARISH_REVERSAL_CONFIRMED")
                else:
                    candidate = DirectionalRegime.TRENDING_DOWN
                    confidence = round(bear_score, 2)

            else:
                candidate = DirectionalRegime.SIDEWAYS
                confidence = round(1.0 - abs(bull_score - bear_score), 2)
                reasons.append("SIDEWAYS_CONSOLIDATION")

            # Apply confirmation bars / regime stability protection
            final_regime = candidate
            if prev_regime is not None and candidate != prev_regime:
                if candidate == pending_regime:
                    confirmation_count += 1
                else:
                    pending_regime = candidate
                    confirmation_count = 1

                if confirmation_count < self.min_confirmation_bars:
                    final_regime = prev_regime  # Hold previous regime until confirmed
                else:
                    final_regime = candidate
                    pending_regime = None
                    confirmation_count = 0
            else:
                pending_regime = None
                confirmation_count = 0

            prev_regime = final_regime

            regime_snap = MarketRegimeSnapshot(
                symbol=snap.symbol,
                timestamp=snap.timestamp,
                timeframe=snap.timeframe,
                directional_regime=final_regime,
                volatility_state=vol_state,
                confidence=confidence,
                reasons=reasons,
                feature_timestamp=snap.timestamp,
                session_state="SIGNAL_ENGINE_ACTIVE",
                validity_status="VALID" if snap.warmup_ready else "WARMUP",
                data_mode="MOCK / SIMULATED DATA",
                provider="mock"
            )
            results.append(regime_snap)

        return results

regime_engine = MarketRegimeEngine()
