from fastapi import APIRouter
from app.api.v1.endpoints import health, market, options, cost, features, regime, prediction, backtest
from app.api.v1 import websocket

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data & Session"])
api_router.include_router(options.router, prefix="/options", tags=["Option Chain"])
api_router.include_router(cost.router, prefix="/costs", tags=["Profitability & Cost Engine"])
api_router.include_router(features.router, prefix="/features", tags=["Feature Engineering"])
api_router.include_router(regime.router, prefix="/regime", tags=["Market Regime Engine"])
api_router.include_router(prediction.router, prefix="/prediction", tags=["ML Prediction Pipeline"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["Backtesting & Prediction Evaluation Engine"])
api_router.include_router(websocket.router, tags=["WebSockets"])
