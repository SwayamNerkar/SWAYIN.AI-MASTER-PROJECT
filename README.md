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
1. **ML Architecture & Interfaces**:
   - `MLModelInterface` (fit, predict, save, load abstraction).
   - `DatasetBuilderInterface` (chronological feature-target matrix construction).
   - `PredictionServiceInterface` (end-to-end inference service).
2. **Dataset Builder (`MLDatasetBuilder`)**:
   - Target: `future_return = (close[t + horizon] - close[t]) / close[t]` ($N$-bars ahead, default $N=3$).
   - Integrates Task 1.3 features and Task 1.4 regime context (`regime_code`, `volatility_code`, `regime_confidence`).
   - **Target Leakage Protection**: Feature matrix $X$ strictly excludes target columns and future rows.
   - **Chronological Split**: `TRAIN` (70%) $\rightarrow$ `VALIDATION` (15%) $\rightarrow$ `TEST` (15%) preserving temporal order (`train_ts < val_ts < test_ts`, zero random shuffling).
3. **Feature Preprocessor (`FeaturePreprocessor`)**:
   - Imputes missing values and scales features (`StandardScaler`).
   - **Mandatory Rule**: Scaler fitted **ONLY** on training set $X_{train}$.
4. **Baseline Model & Training (`GradientBoostingModel` & `ModelTrainingService`)**:
   - Scikit-Learn `GradientBoostingRegressor(n_estimators=100, random_state=42)`.
   - Metrics evaluated: MAE, RMSE, $R^2$, Directional Accuracy.
   - Compared against Naive Zero-Return Baseline (`improves_naive`).
   - Saves versioned artifacts to `backend/ml_models/`.
5. **Prediction API Endpoints**:
   - `GET /api/v1/prediction/nifty` — Returns current ML prediction for NIFTY.
   - `GET /api/v1/prediction/sensex` — Returns current ML prediction for SENSEX.
   - `POST /api/v1/prediction/train` — Triggers development model training.

---

## Current Operational Notice
```text
CURRENT DATA MODE = MOCK / SIMULATED DATA
MODEL STATUS = EXPERIMENTAL
```
- The ML prediction models produce pure numerical predictions (`future_return`). They do **NOT** generate buy/sell trading signals, place orders, or execute trades.
- Real market data APIs, real broker execution, and live trading strategies are NOT connected yet.
- All mock data is clearly labeled `MOCK / SIMULATED DATA`.

---

## How to Run Tests & Server

### 1. Run Complete Test Suite (Task 1.1 + 1.2 + 1.3 + 1.4 + 1.5)
```bash
python -m pytest backend/tests -v
```

### 2. Start Backend Server
```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

### 3. Inspect API Routes
- Swagger UI: `http://localhost:8000/docs`
- NIFTY Prediction: `http://localhost:8000/api/v1/prediction/nifty`
- SENSEX Prediction: `http://localhost:8000/api/v1/prediction/sensex`
