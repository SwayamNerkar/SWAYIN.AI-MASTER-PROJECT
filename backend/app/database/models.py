import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, JSON
from app.database.session import Base

def generate_uuid():
    return str(uuid.uuid4())

class CostConfigurationModel(Base):
    __tablename__ = "cost_configurations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    broker_name = Column(String(50), nullable=False, default="DEFAULT_NSE_OPTIONS")
    brokerage_per_order = Column(Float, nullable=False, default=20.0)
    stt_percent_sell = Column(Float, nullable=False, default=0.00125)
    exchange_txn_charge_percent = Column(Float, nullable=False, default=0.00035)
    gst_percent = Column(Float, nullable=False, default=0.18)
    stamp_duty_percent_buy = Column(Float, nullable=False, default=0.00003)
    sebi_charges_per_crore = Column(Float, nullable=False, default=10.0)
    estimated_slippage_points = Column(Float, nullable=False, default=0.5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketCandleModel(Base):
    __tablename__ = "market_candles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True) # NIFTY / SENSEX
    timeframe = Column(String(10), nullable=False, default="1m")
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    is_simulated = Column(Boolean, default=True)

class OptionChainSnapshotModel(Base):
    __tablename__ = "option_chain_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, index=True)
    underlying = Column(String(20), nullable=False)
    spot_price = Column(Float, nullable=False)
    atm_strike = Column(Float, nullable=False)
    expiry_date = Column(String(20), nullable=False)
    pcr_oi = Column(Float, nullable=False)
    total_ce_oi = Column(Integer, nullable=False)
    total_pe_oi = Column(Integer, nullable=False)
    chain_json = Column(JSON, nullable=False)

class MarketSessionLogModel(Base):
    __tablename__ = "market_session_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    state = Column(String(50), nullable=False)
    trading_date = Column(String(20), nullable=False)
    new_trades_allowed = Column(Boolean, nullable=False)
    message = Column(Text, nullable=True)

class MarketQuoteModel(Base):
    __tablename__ = "market_quotes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    ltp = Column(Float, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    previous_close = Column(Float, nullable=True)
    volume = Column(Integer, default=0)
    provider = Column(String(50), default="mock")
    data_mode = Column(String(50), default="MOCK / SIMULATED DATA")

class DataHealthLogModel(Base):
    __tablename__ = "data_health_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    nifty_fresh = Column(Boolean, nullable=False)
    sensex_fresh = Column(Boolean, nullable=False)
    nifty_age_seconds = Column(Float, nullable=False)
    sensex_age_seconds = Column(Float, nullable=False)
    validation_passed = Column(Boolean, nullable=False, default=True)
    stale_warning = Column(Boolean, nullable=False, default=False)
    provider_healthy = Column(Boolean, nullable=False, default=True)

class FeatureSnapshotModel(Base):
    __tablename__ = "feature_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, default="1m")
    features_json = Column(JSON, nullable=False)
    is_snapshot_valid = Column(Boolean, default=True)
    warmup_ready = Column(Boolean, default=True)
    data_mode = Column(String(50), default="MOCK / SIMULATED DATA")

class MarketRegimeSnapshotModel(Base):
    __tablename__ = "market_regime_snapshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False, default="1m")
    directional_regime = Column(String(30), nullable=False)
    volatility_state = Column(String(20), nullable=False)
    confidence = Column(Float, nullable=False)
    reasons_json = Column(JSON, nullable=False)
    session_state = Column(String(50), nullable=False)
    validity_status = Column(String(30), default="VALID")
    data_mode = Column(String(50), default="MOCK / SIMULATED DATA")

class VolatilityTransitionModel(Base):
    __tablename__ = "volatility_state_transitions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    previous_state = Column(String(20), nullable=False)
    current_state = Column(String(20), nullable=False)
    measured_volatility = Column(Float, nullable=False)
    threshold_used = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)

class MLModelRegistryModel(Base):
    __tablename__ = "ml_model_registry"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(50), nullable=False, unique=True)
    model_name = Column(String(50), nullable=False, default="GradientBoostingRegressor")
    model_version = Column(String(20), nullable=False, default="v1.0.0")
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False, default="1m")
    target_name = Column(String(30), nullable=False, default="future_return")
    horizon_bars = Column(Integer, nullable=False, default=3)
    status = Column(String(30), nullable=False, default="EXPERIMENTAL")
    metrics_json = Column(JSON, nullable=False)
    artifact_path = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class MLTrainingRunModel(Base):
    __tablename__ = "ml_training_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    model_id = Column(String(50), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    training_rows = Column(Integer, nullable=False)
    validation_rows = Column(Integer, nullable=False)
    test_rows = Column(Integer, nullable=False)
    rmse = Column(Float, nullable=False)
    mae = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)
    improves_naive = Column(Boolean, nullable=False)
    run_timestamp = Column(DateTime, default=datetime.utcnow)

class BacktestRunModel(Base):
    __tablename__ = "backtest_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(50), nullable=False, unique=True)
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    model_version = Column(String(20), nullable=False)
    horizon_bars = Column(Integer, nullable=False, default=3)
    walk_forward_mode = Column(String(20), nullable=False, default="EXPANDING")
    prediction_count = Column(Integer, nullable=False)
    mae = Column(Float, nullable=False)
    rmse = Column(Float, nullable=False)
    r2 = Column(Float, nullable=False)
    directional_accuracy = Column(Float, nullable=False)
    improves_naive = Column(Boolean, nullable=False)
    config_json = Column(JSON, nullable=False)
    summary_metrics_json = Column(JSON, nullable=False)
    data_mode = Column(String(50), default="MOCK / SIMULATED DATA")
    created_at = Column(DateTime, default=datetime.utcnow)

class BacktestPredictionModel(Base):
    __tablename__ = "backtest_predictions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    backtest_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    prediction = Column(Float, nullable=False)
    actual = Column(Float, nullable=False)
    prediction_error = Column(Float, nullable=False)
    absolute_error = Column(Float, nullable=False)
    direction_correct = Column(Boolean, nullable=False)
    directional_regime = Column(String(30), nullable=True)
    volatility_state = Column(String(20), nullable=True)





