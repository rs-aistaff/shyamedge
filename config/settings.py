from enum import Enum
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppMode(str, Enum):
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE = "LIVE"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core Execution Mode
    app_mode: AppMode = Field(default=AppMode.PAPER, alias="APP_MODE")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Virtual Portfolio Constraints (Calibrated for NIFTY Lot 65 & SENSEX Lot 20)
    initial_capital: float = Field(default=30000.0, alias="INITIAL_CAPITAL")
    max_risk_per_trade_pct: float = Field(default=0.03, alias="MAX_RISK_PER_TRADE_PCT")  # 3% (₹900)
    max_daily_loss_pct: float = Field(default=0.04, alias="MAX_DAILY_LOSS_PCT")          # 4% (₹1,200)
    max_open_positions: int = Field(default=1, alias="MAX_OPEN_POSITIONS")
    max_trades_per_day: int = Field(default=3, alias="MAX_TRADES_PER_DAY")
    max_consecutive_losses: int = Field(default=2, alias="MAX_CONSECUTIVE_LOSSES")

    # Database & Cache
    database_url: str = Field(default="sqlite:///./shyam_edge.db", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    use_redis: bool = Field(default=False, alias="USE_REDIS")

    # Brokers
    broker_provider: str = Field(default="DHAN", alias="BROKER_PROVIDER")
    dhan_client_id: str = Field(default="", alias="DHAN_CLIENT_ID")
    dhan_access_token: str = Field(default="", alias="DHAN_ACCESS_TOKEN")
    fyers_app_id: str = Field(default="", alias="FYERS_APP_ID")
    fyers_access_token: str = Field(default="", alias="FYERS_ACCESS_TOKEN")

    # Alerts
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")
    enable_telegram_alerts: bool = Field(default=False, alias="ENABLE_TELEGRAM_ALERTS")

    # Slippage & Simulation
    default_slippage_pct: float = Field(default=0.004, alias="DEFAULT_SLIPPAGE_PCT")  # 0.4% default
    round_trip_brokerage: float = Field(default=40.0, alias="ROUND_TRIP_BROKERAGE")

    # Base Paths
    base_dir: Path = Path(__file__).resolve().parent.parent

    @property
    def max_risk_amount(self) -> float:
        """Max planned risk in INR per trade."""
        return self.initial_capital * self.max_risk_per_trade_pct

    @property
    def max_daily_loss_amount(self) -> float:
        """Max allowed daily loss in INR before circuit breaker."""
        return self.initial_capital * self.max_daily_loss_pct

settings = Settings()
