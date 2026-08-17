import datetime
from typing import Dict, Any, List, Optional
from app.schemas.market_data import IndexQuote, OHLCVCandle

class MarketDataValidationError(ValueError):
    """Custom exception raised when market data fails quality or integrity validation."""
    pass

class ValidationService:
    """
    Production Validation Subsystem for Market Data and Option Chains.
    Strictly checks mathematical relationships, bounds, timestamps, and series integrity.
    """

    ALLOWED_SYMBOLS = {"NIFTY", "SENSEX", "INDIAVIX"}
    ALLOWED_INTERVALS = {"1m", "5m", "15m", "30m", "1h", "1d"}

    def validate_quote(self, quote: IndexQuote) -> bool:
        """Validates IndexQuote parameters."""
        if quote.symbol not in self.ALLOWED_SYMBOLS:
            raise MarketDataValidationError(f"Invalid quote symbol '{quote.symbol}'. Allowed: {self.ALLOWED_SYMBOLS}")

        if quote.ltp <= 0:
            raise MarketDataValidationError(f"Invalid LTP {quote.ltp} for symbol {quote.symbol}. Must be positive.")

        if quote.high < quote.low:
            raise MarketDataValidationError(f"Corrupted quote OHLC: High ({quote.high}) < Low ({quote.low})")

        if quote.high < max(quote.open, quote.close, quote.ltp):
            raise MarketDataValidationError(
                f"Corrupted quote High ({quote.high}) is less than max(open, close, ltp)"
            )

        if quote.low > min(quote.open, quote.close, quote.ltp):
            raise MarketDataValidationError(
                f"Corrupted quote Low ({quote.low}) is greater than min(open, close, ltp)"
            )

        if quote.volume is not None and quote.volume < 0:
            raise MarketDataValidationError(f"Negative volume ({quote.volume}) detected for symbol {quote.symbol}")

        return True

    def validate_candle(self, candle: OHLCVCandle) -> bool:
        """
        Validates individual OHLCV Candle structure & mathematical constraints.
        Rules:
        - high >= max(open, close, low)
        - low <= min(open, close, high)
        - high >= low
        - volume >= 0
        - open, high, low, close > 0
        """
        if candle.symbol not in self.ALLOWED_SYMBOLS:
            raise MarketDataValidationError(f"Invalid candle symbol '{candle.symbol}'")

        if candle.interval not in self.ALLOWED_INTERVALS:
            raise MarketDataValidationError(f"Invalid candle interval '{candle.interval}'")

        if any(val <= 0 for val in [candle.open, candle.high, candle.low, candle.close]):
            raise MarketDataValidationError(
                f"Invalid candle non-positive prices: O={candle.open}, H={candle.high}, L={candle.low}, C={candle.close}"
            )

        if candle.high < candle.low:
            raise MarketDataValidationError(
                f"Corrupted candle: High ({candle.high}) < Low ({candle.low})"
            )

        if candle.high < max(candle.open, candle.close, candle.low):
            raise MarketDataValidationError(
                f"Corrupted candle: High ({candle.high}) is less than max(open, close, low)"
            )

        if candle.low > min(candle.open, candle.close, candle.high):
            raise MarketDataValidationError(
                f"Corrupted candle: Low ({candle.low}) is greater than min(open, close, high)"
            )

        if candle.volume < 0:
            raise MarketDataValidationError(f"Negative volume ({candle.volume}) in candle for {candle.symbol}")

        return True

    def validate_candle_series(self, candles: List[OHLCVCandle]) -> bool:
        """
        Validates a series of OHLCV candles for duplicates and time ordering.
        """
        if not candles:
            return True

        seen_timestamps = set()
        prev_ts: Optional[datetime.datetime] = None

        for idx, candle in enumerate(candles):
            self.validate_candle(candle)

            if candle.timestamp in seen_timestamps:
                raise MarketDataValidationError(
                    f"Duplicate timestamp '{candle.timestamp.isoformat()}' found at index {idx} in candle series"
                )
            seen_timestamps.add(candle.timestamp)

            if prev_ts is not None and candle.timestamp < prev_ts:
                raise MarketDataValidationError(
                    f"Out of order timestamp sequence at index {idx}: {candle.timestamp.isoformat()} < {prev_ts.isoformat()}"
                )
            prev_ts = candle.timestamp

        return True

    def validate_option_chain(self, chain_data: Dict[str, Any]) -> bool:
        """
        Validates raw or parsed option chain structure and strike parameters.
        """
        underlying = chain_data.get("underlying", "").upper()
        if underlying not in ("NIFTY", "SENSEX"):
            raise MarketDataValidationError(f"Invalid option chain underlying '{underlying}'")

        spot = chain_data.get("spot_price", 0.0)
        if spot <= 0:
            raise MarketDataValidationError(f"Invalid spot price ({spot}) in option chain for {underlying}")

        chain = chain_data.get("chain", [])
        if not chain:
            raise MarketDataValidationError(f"Option chain for {underlying} is empty")

        for strike_row in chain:
            strike = strike_row.get("strike_price", 0.0)
            if strike <= 0:
                raise MarketDataValidationError(f"Invalid strike price ({strike}) in option chain")

            for opt_type in ("CE", "PE"):
                opt = strike_row.get(opt_type)
                if not opt:
                    raise MarketDataValidationError(f"Missing {opt_type} data for strike {strike}")

                ltp = opt.get("ltp", 0.0)
                if ltp < 0:
                    raise MarketDataValidationError(f"Negative LTP ({ltp}) for {strike} {opt_type}")

                oi = opt.get("oi", 0)
                if oi < 0:
                    raise MarketDataValidationError(f"Negative OI ({oi}) for {strike} {opt_type}")

                iv = opt.get("iv", 0.0)
                if iv < 0:
                    raise MarketDataValidationError(f"Negative IV ({iv}) for {strike} {opt_type}")

        return True

validation_service = ValidationService()
