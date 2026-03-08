"""Global configuration for Portfolio Tracker."""

from pydantic_settings import BaseSettings
from pydantic import Field


class IBKRSettings(BaseSettings):
    """Interactive Brokers connection settings."""

    host: str = "127.0.0.1"
    port: int = 7497  # 7497=TWS paper, 7496=TWS live, 4002=Gateway paper, 4001=Gateway live
    client_id: int = 1
    timeout: float = 30.0
    readonly: bool = False

    model_config = {"env_prefix": "IBKR_"}


class RiskSettings(BaseSettings):
    """Risk management parameters."""

    min_risk_reward_ratio: float = Field(default=2.0, description="Minimum R/R ratio to allow trade execution")
    atr_period: int = Field(default=14, description="ATR lookback period")
    atr_multiplier_min: float = Field(default=1.5, description="Minimum ATR multiplier for stop-loss")
    atr_multiplier_max: float = Field(default=3.0, description="Maximum ATR multiplier for stop-loss")
    atr_multiplier_default: float = Field(default=2.0, description="Default ATR multiplier for stop-loss")
    max_leverage: float = Field(default=3.0, description="Emergency liquidation leverage threshold")
    leverage_step: float = Field(default=0.3, description="Maximum leverage adjustment per rebalance")
    max_position_pct: float = Field(default=0.25, description="Max single position as % of portfolio")

    model_config = {"env_prefix": "RISK_"}


class DatabaseSettings(BaseSettings):
    """Database connection settings."""

    url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/portfolio_tracker"
    echo: bool = False
    pool_size: int = 10

    model_config = {"env_prefix": "DB_"}


class RedisSettings(BaseSettings):
    """Redis cache settings."""

    url: str = "redis://localhost:6379/0"
    quote_ttl: int = 5  # seconds

    model_config = {"env_prefix": "REDIS_"}


class LLMSettings(BaseSettings):
    """AI/LLM integration settings."""

    provider: str = "anthropic"  # anthropic | openai
    api_key: str = ""
    model: str = "claude-sonnet-4-20250514"

    model_config = {"env_prefix": "LLM_"}


class Settings(BaseSettings):
    """Root settings aggregator."""

    ibkr: IBKRSettings = IBKRSettings()
    risk: RiskSettings = RiskSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()


settings = Settings()
