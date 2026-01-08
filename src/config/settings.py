"""Application settings using Pydantic."""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Polymarket API
    polymarket_api_url: str = Field(default="https://api.polymarket.com")
    polymarket_api_key: Optional[str] = None
    polymarket_private_key: Optional[str] = None

    # Database
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="polymarket_trader")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="")

    # Redis
    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_db: int = Field(default=0)

    # Data Sources
    newsapi_key: Optional[str] = None
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = Field(default="polymarket-ai-trader/0.1.0")

    # MLflow
    mlflow_tracking_uri: str = Field(default="http://localhost:5000")
    mlflow_experiment_name: str = Field(default="polymarket_ai_trader")

    # Trading Parameters
    initial_capital: float = Field(default=10000.0)
    min_edge: float = Field(default=0.05)
    min_confidence: float = Field(default=0.60)
    min_liquidity: float = Field(default=1000.0)
    kelly_fraction: float = Field(default=0.25)
    max_position_pct: float = Field(default=0.05)
    max_total_exposure: float = Field(default=0.50)

    # Risk Management
    max_daily_loss: float = Field(default=0.05)
    max_drawdown: float = Field(default=0.15)
    stop_loss_pct: float = Field(default=0.50)

    # Logging
    log_level: str = Field(default="INFO")

    # Paths
    base_dir: Path = Field(default=Path(__file__).parent.parent.parent)
    config_dir: Path = Field(default=Path(__file__).parent.parent.parent / "config")
    data_dir: Path = Field(default=Path(__file__).parent.parent.parent / "data")

    @property
    def database_url(self) -> str:
        """Construct database connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

