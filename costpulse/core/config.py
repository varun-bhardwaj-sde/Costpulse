"""Configuration management for CostPulse."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class DatabricksConfig(BaseSettings):
    """Databricks connection configuration."""

    host: str = Field(...)
    token: str = Field(...)
    account_id: Optional[str] = Field(None)

    class Config:
        """Pydantic configuration."""

        env_prefix = "DATABRICKS_"


class DatabaseConfig(BaseSettings):
    """TimescaleDB database configuration."""

    host: str = Field("localhost", env="TIMESCALE_HOST")
    port: int = Field(5432, env="TIMESCALE_PORT")
    database: str = Field("costpulse", env="TIMESCALE_DB")
    user: str = Field("costpulse", env="TIMESCALE_USER")
    password: str = Field(..., env="TIMESCALE_PASSWORD")

    @property
    def url(self) -> str:
        """Get SQLAlchemy database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseSettings):
    """Redis cache configuration."""

    url: str = Field("redis://localhost:6379/0", env="REDIS_URL")


class Settings(BaseSettings):
    """Global application settings."""

    app_name: str = "CostPulse"
    debug: bool = Field(False, env="DEBUG")
    databricks: DatabricksConfig = DatabricksConfig()
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()

    # Polling interval in seconds
    polling_interval: int = Field(30, env="POLLING_INTERVAL")

    # Feature flags
    enable_forecasting: bool = Field(True, env="ENABLE_FORECASTING")
    enable_anomaly_detection: bool = Field(True, env="ENABLE_ANOMALY_DETECTION")


settings = Settings()
