"""Unit tests for cost calculator."""

import pytest
from decimal import Decimal

from costpulse.processors.cost_calculator import CostCalculator


class TestCostCalculator:
    """Test the CostCalculator class."""

    def test_calculate_dbu_cost_basic(self):
        """Test basic DBU cost calculation."""
        calculator = CostCalculator()

        # Jobs compute: 100 DBUs * $0.15 = $15.00
        cost = calculator.calculate_dbu_cost("JOBS_COMPUTE", 100, photon_enabled=False)
        assert cost == Decimal("15.0")

    def test_calculate_dbu_cost_photon(self):
        """Test DBU cost calculation with Photon enabled."""
        calculator = CostCalculator()

        # Jobs compute with Photon: 100 DBUs * $0.30 = $30.00
        cost = calculator.calculate_dbu_cost("JOBS_COMPUTE", 100, photon_enabled=True)
        assert cost == Decimal("30.0")

    def test_calculate_dbu_cost_serverless_sql(self):
        """Test serverless SQL compute cost calculation."""
        calculator = CostCalculator()

        # Serverless SQL: 100 DBUs * $0.70 = $70.00
        cost = calculator.calculate_dbu_cost("SQL_COMPUTE_SERVERLESS", 100)
        assert cost == Decimal("70.0")

    def test_calculate_dbu_cost_unknown_sku(self):
        """Test cost calculation with unknown SKU uses default rate."""
        calculator = CostCalculator()

        # Unknown SKU should use default rate of $0.15
        cost = calculator.calculate_dbu_cost("UNKNOWN_SKU", 100)
        assert cost == Decimal("15.0")

    def test_calculate_dbu_cost_custom_rates(self):
        """Test cost calculation with custom rates."""
        custom_rates = {"CUSTOM_SKU": 0.50}
        calculator = CostCalculator(custom_rates=custom_rates)

        cost = calculator.calculate_dbu_cost("CUSTOM_SKU", 100)
        assert cost == Decimal("50.0")

    def test_estimate_query_cost_serverless(self):
        """Test query cost estimation for serverless warehouse."""
        calculator = CostCalculator()

        # Serverless, Small warehouse, 1 hour (3600 seconds)
        # $0.70 * 1.0 (Small) * 1 hour = $0.70
        cost = calculator.estimate_query_cost("SERVERLESS", 3600, "Small")
        assert cost == Decimal("0.7")

    def test_estimate_query_cost_large_warehouse(self):
        """Test query cost estimation for large warehouse."""
        calculator = CostCalculator()

        # Classic, Large warehouse (4x multiplier), 1 hour
        # $0.22 * 4.0 (Large) * 1 hour = $0.88
        cost = calculator.estimate_query_cost("CLASSIC", 3600, "Large")
        assert cost == Decimal("0.88")
