"""Custom exceptions for CostPulse."""


class CostPulseError(Exception):
    """Base exception for CostPulse."""

    pass


class ConfigurationError(CostPulseError):
    """Configuration-related errors."""

    pass


class DatabricksConnectionError(CostPulseError):
    """Databricks connection errors."""

    pass


class DataCollectionError(CostPulseError):
    """Data collection errors."""

    pass


class DatabaseError(CostPulseError):
    """Database operation errors."""

    pass


class CalculationError(CostPulseError):
    """Cost calculation errors."""

    pass
