import math
import datetime
from typing import Dict, Any, List, Optional
from app.interfaces.option_chain import OptionChainProvider
from app.adapters.mock.mock_feed import MockMarketDataAdapter

class MockOptionChainAdapter(OptionChainProvider):
    """
    Synthetic Option Chain Generator.
    Generates realistic, mathematically consistent options pricing, IVs, OI, and Greeks
    for NIFTY 50 and SENSEX index options.
    """

    STRIKE_STEPS = {
        "NIFTY": 50,
        "SENSEX": 100
    }
    
    LOT_SIZES = {
        "NIFTY": 25,
        "SENSEX": 10
    }

    def __init__(self, feed: Optional[MockMarketDataAdapter] = None):
        self.feed = feed or MockMarketDataAdapter()

    async def get_atm_strike(self, underlying: str) -> float:
        sym = underlying.upper()
        quote = await self.feed.get_index_quote(sym)
        spot = quote["ltp"]
        step = self.STRIKE_STEPS.get(sym, 50)
        return round(round(spot / step) * step, 2)

    def _estimate_option_premium(
        self, spot: float, strike: float, option_type: str, iv: float = 0.15, dte_days: float = 4.0
    ) -> Dict[str, float]:
        """
        Simplified option pricing model for realistic synthetic premiums & Delta.
        """
        moneyness = (spot - strike) if option_type == "CE" else (strike - spot)
        intrinsic = max(0.0, moneyness)
        
        # Time value approximation based on DTE and IV
        time_factor = math.sqrt(max(0.1, dte_days) / 365.0)
        extrinsic = spot * iv * time_factor * 0.4 * math.exp(-abs(spot - strike) / (spot * 0.05))
        
        premium = round(intrinsic + extrinsic, 2)
        if premium < 0.50:
            premium = 0.50

        # Delta estimate
        distance_pct = (spot - strike) / spot
        if option_type == "CE":
            delta = 0.5 + (distance_pct * 10)
            delta = max(0.05, min(0.95, delta))
        else:
            delta = -0.5 + (distance_pct * 10)
            delta = min(-0.05, max(-0.95, delta))

        return {
            "premium": round(premium, 2),
            "delta": round(delta, 3),
            "iv": round(iv * 100, 2),
            "intrinsic": round(intrinsic, 2),
            "extrinsic": round(extrinsic, 2)
        }

    async def get_option_chain(self, underlying: str, expiry: Optional[str] = None) -> Dict[str, Any]:
        sym = underlying.upper()
        quote = await self.feed.get_index_quote(sym)
        spot = quote["ltp"]
        step = self.STRIKE_STEPS.get(sym, 50)
        atm_strike = await self.get_atm_strike(sym)
        
        if not expiry:
            # Default to nearest Thursday expiry string
            today = datetime.date.today()
            days_ahead = 3 - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_thursday = today + datetime.timedelta(days=days_ahead)
            expiry = next_thursday.strftime("%Y-%m-%d")

        strikes_count = 7  # 7 strikes below ATM, ATM, 7 strikes above ATM
        strikes = [atm_strike + (i * step) for i in range(-strikes_count, strikes_count + 1)]

        chain = []
        total_ce_oi = 0
        total_pe_oi = 0

        for strike in strikes:
            # CE option calculation
            ce_data = self._estimate_option_premium(spot, strike, "CE")
            ce_oi = int(max(1000, (100000 - abs(spot - strike) * 40)))
            ce_change_oi = int(ce_oi * 0.08 * (1 if spot > strike else -0.5))
            total_ce_oi += ce_oi

            # PE option calculation
            pe_data = self._estimate_option_premium(spot, strike, "PE")
            pe_oi = int(max(1000, (100000 - abs(spot - strike) * 40)))
            pe_change_oi = int(pe_oi * 0.08 * (1 if spot < strike else -0.5))
            total_pe_oi += pe_oi

            is_atm = (strike == atm_strike)

            chain.append({
                "strike_price": strike,
                "is_atm": is_atm,
                "moneyness": "ATM" if is_atm else ("ITM" if spot > strike else "OTM"),
                "CE": {
                    "symbol": f"{sym}{strike}CE",
                    "option_type": "CE",
                    "ltp": ce_data["premium"],
                    "bid": round(ce_data["premium"] - 0.25, 2),
                    "ask": round(ce_data["premium"] + 0.25, 2),
                    "iv": ce_data["iv"],
                    "delta": ce_data["delta"],
                    "volume": int(ce_oi * 0.35),
                    "oi": ce_oi,
                    "change_in_oi": ce_change_oi
                },
                "PE": {
                    "symbol": f"{sym}{strike}PE",
                    "option_type": "PE",
                    "ltp": pe_data["premium"],
                    "bid": round(pe_data["premium"] - 0.25, 2),
                    "ask": round(pe_data["premium"] + 0.25, 2),
                    "iv": pe_data["iv"],
                    "delta": pe_data["delta"],
                    "volume": int(pe_oi * 0.35),
                    "oi": pe_oi,
                    "change_in_oi": pe_change_oi
                }
            })

        pcr = round(total_pe_oi / total_ce_oi, 2) if total_ce_oi > 0 else 1.0

        return {
            "underlying": sym,
            "spot_price": spot,
            "atm_strike": atm_strike,
            "expiry_date": expiry,
            "lot_size": self.LOT_SIZES.get(sym, 25),
            "pcr_oi": pcr,
            "total_ce_oi": total_ce_oi,
            "total_pe_oi": total_pe_oi,
            "chain": chain,
            "timestamp": datetime.datetime.now().isoformat(),
            "data_mode": "MOCK / SIMULATED DATA"
        }

    async def get_option_quote(self, option_symbol: str) -> Dict[str, Any]:
        # Fast lookup mock quote
        return {
            "symbol": option_symbol,
            "ltp": 185.50,
            "bid": 185.25,
            "ask": 185.75,
            "iv": 15.2,
            "delta": 0.52,
            "volume": 45000,
            "oi": 850000,
            "is_simulated": True
        }
