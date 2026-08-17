import logging
import datetime
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings
from app.schemas.features import FeatureSnapshot
from app.schemas.regime import VolatilityState, VolatilityTransitionLog

logger = logging.getLogger("swayin")

class VolatilityStateMachine:
    """
    Production Volatility State Machine.
    Evaluates LOW, MEDIUM, and HIGH volatility states with hysteresis stabilization.
    Tracks transitions to prevent noisy single-bar state flickering.
    """

    def __init__(
        self,
        low_threshold: float = settings.VOLATILITY_LOW_THRESHOLD,
        high_threshold: float = settings.VOLATILITY_HIGH_THRESHOLD,
        hysteresis_factor: float = settings.VOLATILITY_HYSTERESIS_FACTOR
    ):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold
        self.hysteresis_factor = hysteresis_factor
        self._current_state: Dict[str, VolatilityState] = {}  # Per-symbol state tracking
        self.transition_history: List[VolatilityTransitionLog] = []

    def _get_measured_volatility(self, snapshot: FeatureSnapshot) -> float:
        """Extracts normalized ATR or relative volatility metric from feature snapshot."""
        feats = snapshot.features
        # Primary metric: normalized_atr (ATR as % of Close)
        norm_atr = feats.get("normalized_atr")
        if norm_atr is not None and not math.isnan(norm_atr):
            return float(norm_atr)
        
        # Fallback metric: high_low_range_pct
        hl_range = feats.get("high_low_range_pct")
        if hl_range is not None and not math.isnan(hl_range):
            return float(hl_range)

        return 1.2  # Default baseline medium value if feature missing

    def evaluate_state(
        self,
        snapshot: FeatureSnapshot
    ) -> Tuple[VolatilityState, Optional[VolatilityTransitionLog]]:
        """
        Evaluates state transition using hysteresis buffers.
        Returns (current_state, optional_transition_log).
        """
        sym = snapshot.symbol
        measured_vol = self._get_measured_volatility(snapshot)
        prev_state = self._current_state.get(sym, VolatilityState.MEDIUM)

        low_up = self.low_threshold * (1.0 + self.hysteresis_factor)
        low_down = self.low_threshold * (1.0 - self.hysteresis_factor)
        high_up = self.high_threshold * (1.0 + self.hysteresis_factor)
        high_down = self.high_threshold * (1.0 - self.hysteresis_factor)

        new_state = prev_state
        threshold_triggered = 0.0
        reason = ""

        if prev_state == VolatilityState.LOW:
            if measured_vol >= high_up:
                new_state = VolatilityState.HIGH
                threshold_triggered = high_up
                reason = f"Volatility spike ({measured_vol:.2f}% >= {high_up:.2f}%) triggered LOW -> HIGH transition"
            elif measured_vol >= low_up:
                new_state = VolatilityState.MEDIUM
                threshold_triggered = low_up
                reason = f"Volatility expansion ({measured_vol:.2f}% >= {low_up:.2f}%) triggered LOW -> MEDIUM transition"

        elif prev_state == VolatilityState.MEDIUM:
            if measured_vol >= high_up:
                new_state = VolatilityState.HIGH
                threshold_triggered = high_up
                reason = f"Volatility surge ({measured_vol:.2f}% >= {high_up:.2f}%) triggered MEDIUM -> HIGH transition"
            elif measured_vol <= low_down:
                new_state = VolatilityState.LOW
                threshold_triggered = low_down
                reason = f"Volatility contraction ({measured_vol:.2f}% <= {low_down:.2f}%) triggered MEDIUM -> LOW transition"

        elif prev_state == VolatilityState.HIGH:
            if measured_vol <= low_down:
                new_state = VolatilityState.LOW
                threshold_triggered = low_down
                reason = f"Volatility crash ({measured_vol:.2f}% <= {low_down:.2f}%) triggered HIGH -> LOW transition"
            elif measured_vol <= high_down:
                new_state = VolatilityState.MEDIUM
                threshold_triggered = high_down
                reason = f"Volatility cooling ({measured_vol:.2f}% <= {high_down:.2f}%) triggered HIGH -> MEDIUM transition"

        transition_log = None
        if new_state != prev_state:
            transition_log = VolatilityTransitionLog(
                symbol=sym,
                timestamp=snapshot.timestamp,
                previous_state=prev_state,
                current_state=new_state,
                measured_volatility=round(measured_vol, 2),
                threshold_used=round(threshold_triggered, 2),
                reason=reason
            )
            self.transition_history.append(transition_log)
            self._current_state[sym] = new_state
            logger.info(f"VOLATILITY TRANSITION [{sym}]: {prev_state.value} -> {new_state.value} ({reason})")

        return new_state, transition_log

import math
volatility_state_machine = VolatilityStateMachine()
