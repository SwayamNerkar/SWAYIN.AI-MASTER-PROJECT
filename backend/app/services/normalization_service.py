import datetime
from typing import Dict, Any, Union, Optional
import pytz

class NormalizationService:
    """
    Production Normalization Layer for Market Data.
    Ensures provider-independent internal representations across timestamps, symbols, and numeric fields.
    """

    IST = pytz.timezone("Asia/Kolkata")

    SYMBOL_MAP = {
        "NIFTY": "NIFTY",
        "NIFTY 50": "NIFTY",
        "NIFTY50": "NIFTY",
        "^NSEI": "NIFTY",
        "NSE:NIFTY50-INDEX": "NIFTY",
        "SENSEX": "SENSEX",
        "BSESN": "SENSEX",
        "^BSESN": "SENSEX",
        "BSE:SENSEX-INDEX": "SENSEX",
        "INDIAVIX": "INDIAVIX",
        "INDIA VIX": "INDIAVIX",
        "VIX": "INDIAVIX"
    }

    def normalize_symbol(self, raw_symbol: str) -> str:
        """Converts vendor-specific symbol strings into internal standard representation."""
        if not raw_symbol:
            return "NIFTY"
        cleaned = raw_symbol.strip().upper()
        return self.SYMBOL_MAP.get(cleaned, cleaned)

    def normalize_timestamp(self, raw_ts: Union[str, datetime.datetime, int, float]) -> datetime.datetime:
        """
        Converts any timestamp input (ISO string, unix epoch, naive datetime)
        to a localized Asia/Kolkata datetime object.
        """
        if isinstance(raw_ts, (int, float)):
            # Epoch timestamp in seconds or ms
            if raw_ts > 1e11:  # Epoch in milliseconds
                raw_ts = raw_ts / 1000.0
            dt = datetime.datetime.fromtimestamp(raw_ts, tz=datetime.timezone.utc)
            return dt.astimezone(self.IST)

        if isinstance(raw_ts, str):
            # Parse ISO formatted strings
            cleaned_ts = raw_ts.replace("Z", "+00:00")
            dt = datetime.datetime.fromisoformat(cleaned_ts)
            if dt.tzinfo is None:
                return self.IST.localize(dt)
            return dt.astimezone(self.IST)

        if isinstance(raw_ts, datetime.datetime):
            if raw_ts.tzinfo is None:
                return self.IST.localize(raw_ts)
            return raw_ts.astimezone(self.IST)

        # Fallback to current IST time
        return datetime.datetime.now(self.IST)

    def normalize_interval(self, interval_str: str) -> str:
        """Normalizes timeframe strings ('1m', '5m', '15m', '1d')."""
        if not interval_str:
            return "1m"
        s = interval_str.lower().strip()
        if s in ("1", "1m", "1min", "minute"):
            return "1m"
        if s in ("5", "5m", "5min"):
            return "5m"
        if s in ("15", "15m", "15min"):
            return "15m"
        if s in ("d", "1d", "day", "daily"):
            return "1d"
        return "1m"

    def normalize_quote_dict(self, raw_quote: Dict[str, Any], provider: str = "mock") -> Dict[str, Any]:
        """Normalizes a raw quote dictionary into clean internal structure."""
        symbol = self.normalize_symbol(raw_quote.get("symbol", "NIFTY"))
        ts = self.normalize_timestamp(raw_quote.get("timestamp"))
        
        ltp = round(float(raw_quote.get("ltp", 0.0)), 2)
        open_p = round(float(raw_quote.get("open", ltp)), 2)
        high_p = round(float(raw_quote.get("high", max(open_p, ltp))), 2)
        low_p = round(float(raw_quote.get("low", min(open_p, ltp))), 2)
        close_p = round(float(raw_quote.get("close", ltp)), 2)
        prev_close = float(raw_quote.get("previous_close", close_p)) if raw_quote.get("previous_close") is not None else close_p
        
        change = round(ltp - prev_close, 2)
        change_pct = round((change / prev_close) * 100, 2) if prev_close > 0 else 0.0

        return {
            "symbol": symbol,
            "timestamp": ts,
            "ltp": ltp,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "previous_close": round(prev_close, 2),
            "change": change,
            "change_percent": change_pct,
            "volume": int(raw_quote.get("volume", 0)),
            "data_mode": raw_quote.get("data_mode", "MOCK / SIMULATED DATA"),
            "provider": provider,
            "timezone": "Asia/Kolkata"
        }

    def normalize_candle_dict(self, raw_candle: Dict[str, Any], provider: str = "mock") -> Dict[str, Any]:
        """Normalizes a raw candle dictionary into clean internal structure."""
        symbol = self.normalize_symbol(raw_candle.get("symbol", "NIFTY"))
        ts = self.normalize_timestamp(raw_candle.get("timestamp"))
        interval = self.normalize_interval(raw_candle.get("interval", raw_candle.get("timeframe", "1m")))

        open_p = round(float(raw_candle.get("open", 0.0)), 2)
        high_p = round(float(raw_candle.get("high", 0.0)), 2)
        low_p = round(float(raw_candle.get("low", 0.0)), 2)
        close_p = round(float(raw_candle.get("close", 0.0)), 2)
        volume = int(raw_candle.get("volume", 0))

        return {
            "symbol": symbol,
            "timestamp": ts,
            "interval": interval,
            "open": open_p,
            "high": high_p,
            "low": low_p,
            "close": close_p,
            "volume": volume,
            "data_mode": raw_candle.get("data_mode", "MOCK / SIMULATED DATA"),
            "provider": provider
        }

normalization_service = NormalizationService()
