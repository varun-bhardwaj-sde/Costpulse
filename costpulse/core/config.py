"""Configuration management for CostPulse."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class DatabricksConfig(BaseSettings):
    """Databricks connection configuration."""

    model_config = SettingsConfigDict(env_prefix="DATABRICKS_")

    host: str = Field(default="https://localhost")
    token: str = Field(default="")
    account_id: Optional[str] = Field(default=None)


class DatabaseConfig(BaseSettings):
    """TimescaleDB database configuration."""

    model_config = SettingsConfigDict(env_prefix="TIMESCALE_")

    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="costpulse", alias="TIMESCALE_DB")
    user: str = Field(default="costpulse")
    password: str = Field(default="costpulse_dev")

    @property
    def url(self) -> str:
        """Get SQLAlchemy database URL."""
        return str(
            URL.create(
                drivername="postgresql+asyncpg",
                username=self.user,
                password=self.password,
                host=self.host,
                port=self.port,
                database=self.database,
            )
        )


class RedisConfig(BaseSettings):
    """Redis cache configuration."""

    url: str = Field(default="redis://localhost:6379/0")

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class Settings(BaseSettings):
    """Global application settings."""

    app_name: str = "CostPulse"
    debug: bool = Field(default=False)
    databricks: DatabricksConfig = Field(default_factory=DatabricksConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Polling interval in minutes
    polling_interval: int = Field(default=30)

    # Feature flags
    enable_forecasting: bool = Field(default=True)
    enable_anomaly_detection: bool = Field(default=True)


settings = Settings()
