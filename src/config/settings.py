"""Application settings using Pydantic."""

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
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
    # Support both individual variables and DATABASE_URL (Railway provides DATABASE_URL)
    # If DATABASE_URL is set, it takes precedence over individual variables
    database_url_env: Optional[str] = Field(default=None, alias="DATABASE_URL")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="polymarket_trader")
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="")
    
    @field_validator('postgres_port', mode='before')
    @classmethod
    def parse_postgres_port(cls, v: any) -> int:
        """Parse port value, handling malformed strings from Railway.
        
        Handles cases where Railway sets values like '(usually 5432)' or ' (usually 5432)'
        by extracting the first number found in the string.
        """
        if isinstance(v, int):
            return v
        if isinstance(v, str):
            # Strip whitespace
            v = v.strip()
            # Extract first number from string (handles cases like "(usually 5432)" -> 5432)
            match = re.search(r'\d+', v)
            if match:
                return int(match.group())
            # If no number found, return default
            return 5432
        return 5432

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
    min_confidence: float = Field(default=0.55)  # Lowered from 0.60 to 0.55 to allow more signals
    min_liquidity: float = Field(default=500.0)  # Lowered from 1000.0 to 500.0 to allow more markets
    kelly_fraction: float = Field(default=0.25)
    max_position_pct: float = Field(default=0.05)
    max_total_exposure: float = Field(default=0.50)
    paper_trading_mode: bool = Field(default=True)  # Default to paper trading for demo/sharing

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
        """Construct database connection URL.
        
        Supports both Railway's DATABASE_URL and individual connection parameters.
        Railway provides DATABASE_URL which can be used directly.
        Handles Railway's default PostgreSQL setup where username/password might be empty.
        """
        # If DATABASE_URL is provided (Railway), use it after converting to asyncpg format
        if self.database_url_env and self.database_url_env.startswith("postgresql://"):
            db_url = self.database_url_env
            
            # Fix empty username/password in Railway's DATABASE_URL
            # Railway might provide: postgresql://:@host:port/db or postgresql://host:port/db
            # Pattern: postgresql://:@host or postgresql://:@host:port
            if re.match(r'postgresql://:@', db_url):
                # Replace empty creds with default Railway PostgreSQL user
                # Railway PostgreSQL default user is "postgres"
                # Try to extract password from individual variables if available
                password = self.postgres_password or os.environ.get("POSTGRES_PASSWORD") or os.environ.get("PGPASSWORD") or ""
                user = self.postgres_user or os.environ.get("POSTGRES_USER") or os.environ.get("PGUSER") or "postgres"
                # Replace postgresql://:@ with postgresql://user:password@
                db_url = db_url.replace("postgresql://:@", f"postgresql://{user}:{password}@", 1)
            
            # Convert postgresql:// to postgresql+asyncpg:// for SQLAlchemy async
            return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        
        # Otherwise construct from individual parameters
        # Use defaults if empty (Railway PostgreSQL defaults)
        user = self.postgres_user or "postgres"
        password = self.postgres_password or ""
        host = self.postgres_host or "localhost"
        port = self.postgres_port or 5432
        db = self.postgres_db or "railway"  # Railway's default database name
        
        return (
            f"postgresql+asyncpg://{user}:{password}"
            f"@{host}:{port}/{db}"
        )

    @property
    def redis_url(self) -> str:
        """Construct Redis connection URL."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

