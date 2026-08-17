from fastapi import APIRouter
from app.engines.cost_engine import cost_engine
from app.schemas.cost import CalculateCostRequest

router = APIRouter()

@router.get("/config")
async def get_cost_config():
    return {
        "active_fee_matrix": cost_engine.config,
        "engine_version": "1.1.0"
    }

@router.post("/calculate")
async def calculate_cost(req: CalculateCostRequest):
    return cost_engine.calculate_trade_cost(
        symbol=req.symbol,
        entry_price=req.entry_price,
        exit_price=req.exit_price,
        quantity=req.quantity,
        custom_slippage_pts=req.custom_slippage_pts
    )
