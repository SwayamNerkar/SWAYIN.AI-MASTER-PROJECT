from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "SWAYIN.AI"
    VERSION: str = "1.1.0"
    ENV: str = "development"
    DEBUG: bool = True
    TIMEZONE: str = "Asia/Kolkata"

    # Capital & Risk Defaults
    INITIAL_CAPITAL: float = 20000.0
    MAX_RISK_PER_TRADE_PCT: float = 2.0
    MAX_DAILY_LOSS: float = 1000.0
    MAX_OPEN_POSITIONS: int = 1
    MIN_EXPECTED_NET_PROFIT: float = 300.0
    MIN_RISK_REWARD: float = 1.5

    # Data & Broker Adapter Modes
    DATA_FEED_MODE: str = "MOCK"
    BROKER_ADAPTER: str = "MOCK"
    PAPER_TRADING_ENABLED: bool = True

    # Market Data Subsystem Config (Task 1.2)
    MARKET_DATA_PROVIDER: str = "mock"
    MARKET_DATA_CACHE_ENABLED: bool = True
    MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS: float = 10.0
    MARKET_DATA_DEFAULT_INTERVAL: str = "1m"

    # Technical Indicator & Feature Config (Task 1.3)
    SMA_PERIODS: List[int] = Field(default_factory=lambda: [10, 20, 50])
    EMA_PERIODS: List[int] = Field(default_factory=lambda: [9, 21, 50])
    RSI_PERIOD: int = 14
    ATR_PERIOD: int = 14
    ADX_PERIOD: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    STOCHASTIC_K: int = 14
    STOCHASTIC_D: int = 3
    ROC_PERIOD: int = 12
    VWAP_ENABLED: bool = True

    # Market Regime & Volatility Machine Config (Task 1.4)
    REGIME_ADX_THRESHOLD: float = 20.0
    REGIME_TREND_SCORE_THRESHOLD: float = 0.60
    REGIME_REVERSAL_THRESHOLD: float = 0.65
    REGIME_MIN_CONFIRMATION_BARS: int = 2
    VOLATILITY_LOW_THRESHOLD: float = 1.0
    VOLATILITY_HIGH_THRESHOLD: float = 2.5
    VOLATILITY_HYSTERESIS_FACTOR: float = 0.15

    # Machine Learning Prediction Pipeline Config (Task 1.5)
    ML_DEFAULT_MODEL: str = "gradient_boosting"
    ML_TRAIN_RATIO: float = 0.70
    ML_VALIDATION_RATIO: float = 0.15
    ML_TEST_RATIO: float = 0.15
    ML_RANDOM_SEED: int = 42
    ML_DEFAULT_HORIZON: int = 3
    ML_ARTIFACT_PATH: str = Field(default=str(BASE_DIR / "ml_models"))
    ML_MIN_TRAINING_ROWS: int = 40

    # Backtesting & Prediction Evaluation Engine Config (Task 1.6)
    BACKTEST_DEFAULT_MODE: str = "EXPANDING"
    BACKTEST_INITIAL_TRAIN_BARS: int = 100
    BACKTEST_EVAL_WINDOW_BARS: int = 10
    BACKTEST_RETRAIN_FREQUENCY: str = "window"
    BACKTEST_MIN_TRAINING_ROWS: int = 40
    BACKTEST_MAX_PREDICTIONS: int = 10000

    # Databases
    DATABASE_URL: str = "postgresql+asyncpg://swayin_user:swayin_pass@localhost:5432/swayin_db"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Path to cost configuration JSON
    COST_CONFIG_PATH: str = Field(default=str(BASE_DIR / "config" / "cost_structure.json"))

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
