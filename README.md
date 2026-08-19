# SWAYIN.AI — AI-Based Intraday Options Signal & Market Intelligence System

## Primary Markets
- **NIFTY 50**
- **SENSEX**

## Trading Style
- Intraday only (09:00 - 15:30 IST)
- Options Buying only (CE / PE)
- No option selling
- No overnight positions
- Manual trade execution initially (Groww adapter interface stub initialized for future connection)

---

## Architecture Stack

### Task 1.1 Baseline
- **Broker Abstraction Layer**: Pure `BrokerInterface` abstract base class preventing broker lock-in.
- **Mock Broker Adapter**: `MockBrokerAdapter` paper trading capital manager.
- **Groww Adapter STUB**: Safe non-operational stub (`GrowwAdapter`).
- **Market Session State Machine**: `MarketSessionEngine` (09:00 - 15:30 IST, 8 operational states).
- **Configurable Cost Engine**: `ProfitabilityCostEngine` (`config/cost_structure.json`).

### Task 1.2 Market Data Subsystem
- **Domain Models**: `IndexQuote`, `OHLCVCandle`, `DataHealthStatus`, `MarketSnapshot`, `ValidatedOptionChain`.
- **Normalization Layer**: `NormalizationService` (symbols, Asia/Kolkata timezone, precision).
- **Validation Subsystem**: `ValidationService` (OHLC bounds, timestamp continuity, option chain parameters).
- **Freshness Check**: Configurable threshold (`10.0s`) tracking data age and flagging stale ticks.
- **Caching Layer**: In-memory `MarketDataCacheService` (Redis-ready abstraction).
- **Market Snapshot Service**: Unified `MarketSnapshot` combining NIFTY, SENSEX, session state, and data health status.

### Task 1.3 Feature Engineering & Technical Indicators
- **Feature Engineering Subsystem (`FeatureEngineeringService`)**: Transforms validated OHLCV series into timestamp-aligned numerical features.
- **Technical Indicators**: Price, Trend (SMA, EMA, VWAP, MACD, ADX), Momentum (RSI, ROC, Stochastic), Volatility (ATR, Rolling Std, Realized Vol), Volume, Price-Action.
- **Multi-Timeframe**: Supports `1m` and `5m` timeframes with strict timestamp alignment.
- **Look-Ahead Bias Protection**: Guaranteed zero look-ahead bias verified by automated leakage tests.

### Task 1.4 Market Regime Engine & Volatility State Machine
- **Market Regime Engine (`MarketRegimeEngine`)**: Classifies market context into 5 primary directional regimes (`TRENDING_UP`, `TRENDING_DOWN`, `SIDEWAYS`, `HIGH_VOLATILITY`, `REVERSAL`).
- **Volatility State Machine (`VolatilityStateMachine`)**: Classifies volatility state into `LOW`, `MEDIUM`, and `HIGH` with 15% hysteresis stabilization buffer zone.
- **Regime Stability & Hysteresis**: Confirmation bars requirement (`REGIME_MIN_CONFIRMATION_BARS = 2`).
- **Confidence & Reason Codes**: Evidence agreement confidence ($0.0 \dots 1.0$) and machine-readable reason codes.

### Task 1.5 Machine Learning Prediction Pipeline
- **ML Architecture & Interfaces**: `MLModelInterface`, `DatasetBuilderInterface`, `PredictionServiceInterface`.
- **Dataset Builder (`MLDatasetBuilder`)**: Target $f(t) = \frac{\text{close}[t+N] - \text{close}[t]}{\text{close}[t]}$ ($N=3$ bars).
- **Target Leakage Protection**: Feature matrix $X$ strictly excludes target columns and future rows.
- **Chronological Split**: `TRAIN` (70%) $\rightarrow$ `VALIDATION` (15%) $\rightarrow$ `TEST` (15%) with zero random shuffling.
- **Preprocessing Pipeline (`FeaturePreprocessor`)**: Scaler fitted **ONLY** on training set $X_{train}$.
- **Baseline Model & Training (`GradientBoostingModel` & `ModelTrainingService`)**: Scikit-Learn `GradientBoostingRegressor(n_estimators=100)`.

### Task 1.6 Backtesting, Walk-Forward Validation & Prediction Evaluation Engine
1. **Walk-Forward Evaluation Engine (`WalkForwardBacktestEngine`)**:
   - Implements `BacktestEngineInterface`.
   - Executes expanding-window walk-forward training & prediction evaluation.
   - For each step $k$: `FeaturePreprocessor` and `GradientBoostingModel` are trained **STRICTLY ONLY** on the expanding historical training slice $X_{\text{train}}[0 \dots t]$.
   - Generates individual `BacktestPredictionRecord`s comparing predicted return vs actual future outcome.
   - **Zero Future Leakage**: Modifying candles after timestamp $t$ does NOT alter past predictions at or before $t$.
2. **Statistical & Subgroup Performance Analysis**:
   - **Regression Metrics**: MAE, RMSE, $R^2$, Mean Error, Median Absolute Error, Max Absolute Error.
   - **Directional Metrics**: Directional Accuracy ($\text{sign}(pred) == \text{sign}(actual)$).
   - **Naive Baseline Comparison**: Evaluates model metrics vs Naive Zero-Return Baseline ($pred = 0$) and computes `improves_naive` status.
   - **Task 1.4 Regime Breakdown**: MAE, RMSE, and Directional Accuracy for `TRENDING_UP`, `TRENDING_DOWN`, `SIDEWAYS`, `HIGH_VOLATILITY`, and `REVERSAL`.
   - **Task 1.4 Volatility Breakdown**: Metrics for `LOW`, `MEDIUM`, and `HIGH` volatility states.
   - **Residual & Error Analysis**: Prediction bias, mean prediction, mean actual, max consecutive directional errors.
3. **Backtest REST API Endpoints**:
   - `POST /api/v1/backtest/run` — Executes walk-forward backtest evaluation run.
   - `GET /api/v1/backtest` — Lists recent backtest evaluation summaries.
   - `GET /api/v1/backtest/{backtest_id}` — Fetches complete backtest evaluation report.
   - `GET /api/v1/backtest/{backtest_id}/predictions` — Returns paginated prediction records.

---

## Current Operational Notice
```text
CURRENT DATA MODE = MOCK / SIMULATED DATA
BACKTEST ENGINE STATUS = EVALUATION ONLY (NO LIVE TRADING / NO P&L)
```
- Task 1.6 evaluates **prediction quality vs actual outcomes**. It does **NOT** calculate trading P&L, execute live trades, place broker orders, or generate buy/sell signals.
- All mock data is clearly labeled `MOCK / SIMULATED DATA`.

---

## How to Run Tests & Server

### 1. Run Complete Test Suite (Task 1.1 + 1.2 + 1.3 + 1.4 + 1.5 + 1.6)
```bash
python -m pytest backend/tests -v
```

### 2. Start Backend Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

### 3. Inspect API Routes
- Swagger UI: `http://localhost:8000/docs`
- Run Backtest: `POST http://localhost:8000/api/v1/backtest/run`
- List Backtests: `GET http://localhost:8000/api/v1/backtest`
