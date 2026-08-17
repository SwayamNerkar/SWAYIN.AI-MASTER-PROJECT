import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from app.core.config import settings

class CostBreakdown(BaseModel):
    symbol: str
    quantity: int
    entry_price: float
    exit_price: float
    buy_turnover: float
    sell_turnover: float
    total_turnover: float
    gross_pnl: float
    brokerage: float
    stt: float
    exchange_txn_charge: float
    gst: float
    stamp_duty: float
    sebi_charges: float
    slippage: float
    total_charges: float
    net_pnl: float
    is_profitable: bool
    net_pnl_pct: float

class ProfitabilityCostEngine:
    """
    Configurable Production-Grade Cost & Charges Engine for Indian Index Options Buying.
    
    Fee Matrix Supported:
    1. Flat Brokerage per order (Entry + Exit)
    2. STT (Securities Transaction Tax) - Charged on Option Premium when Selling/Closing
    3. Exchange Transaction Charges (NSE/BSE) - Percentage on Premium turnover
    4. GST - 18% applied to (Brokerage + Exchange Txn Charges)
    5. Stamp Duty - Charged on Buy value
    6. SEBI Turnover Fees - Per Crore calculation
    7. Slippage - Configurable point slippage per contract lot
    """

    def __init__(self, config_path: Optional[str] = None):
        path = config_path or settings.COST_CONFIG_PATH
        self.config = self._load_config(path)

    def _load_config(self, path: str) -> Dict[str, Any]:
        p = Path(path)
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        # Default fallback fee structure if file missing
        return {
            "brokerage_per_order": 20.0,
            "stt_percent_sell": 0.00125,
            "exchange_txn_charge_percent": 0.00035,
            "gst_percent": 0.18,
            "stamp_duty_percent_buy": 0.00003,
            "sebi_charges_per_crore": 10.0,
            "estimated_slippage_points": 0.5,
            "lot_sizes": {"NIFTY": 25, "SENSEX": 10}
        }

    def calculate_trade_cost(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        quantity: int,
        custom_slippage_pts: Optional[float] = None
    ) -> CostBreakdown:
        """
        Calculates detailed itemized trading charges, gross P&L, and net P&L.
        """
        buy_turnover = round(entry_price * quantity, 2)
        sell_turnover = round(exit_price * quantity, 2)
        total_turnover = round(buy_turnover + sell_turnover, 2)

        # 1. Gross P&L
        gross_pnl = round(sell_turnover - buy_turnover, 2)

        # 2. Brokerage (Flat fee for Entry + Flat fee for Exit)
        brokerage_rate = self.config.get("brokerage_per_order", 20.0)
        brokerage = round(brokerage_rate * 2.0, 2)

        # 3. STT (Applied on option sell premium)
        stt_rate = self.config.get("stt_percent_sell", 0.00125)
        stt = round(sell_turnover * stt_rate, 2)

        # 4. Exchange Transaction Charges (Applied on total premium turnover)
        exch_rate = self.config.get("exchange_txn_charge_percent", 0.00035)
        exchange_txn_charge = round(total_turnover * exch_rate, 2)

        # 5. GST (18% on Brokerage + Exchange Txn Charge)
        gst_rate = self.config.get("gst_percent", 0.18)
        gst = round((brokerage + exchange_txn_charge) * gst_rate, 2)

        # 6. Stamp Duty (Applied on buy turnover)
        stamp_rate = self.config.get("stamp_duty_percent_buy", 0.00003)
        stamp_duty = round(buy_turnover * stamp_rate, 2)

        # 7. SEBI Charges (₹10 per crore = turnover / 1,000,000)
        sebi_rate = self.config.get("sebi_charges_per_crore", 10.0) / 10000000.0
        sebi_charges = round(total_turnover * sebi_rate, 2)

        # 8. Slippage Cost
        slippage_pts = custom_slippage_pts if custom_slippage_pts is not None else self.config.get("estimated_slippage_points", 0.5)
        slippage = round(slippage_pts * quantity, 2)

        # Sum of all costs
        total_charges = round(
            brokerage + stt + exchange_txn_charge + gst + stamp_duty + sebi_charges + slippage, 2
        )

        # Net P&L
        net_pnl = round(gross_pnl - total_charges, 2)
        is_profitable = (net_pnl > 0)
        net_pnl_pct = round((net_pnl / buy_turnover) * 100, 2) if buy_turnover > 0 else 0.0

        return CostBreakdown(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            exit_price=exit_price,
            buy_turnover=buy_turnover,
            sell_turnover=sell_turnover,
            total_turnover=total_turnover,
            gross_pnl=gross_pnl,
            brokerage=brokerage,
            stt=stt,
            exchange_txn_charge=exchange_txn_charge,
            gst=gst,
            stamp_duty=stamp_duty,
            sebi_charges=sebi_charges,
            slippage=slippage,
            total_charges=total_charges,
            net_pnl=net_pnl,
            is_profitable=is_profitable,
            net_pnl_pct=net_pnl_pct
        )

cost_engine = ProfitabilityCostEngine()
