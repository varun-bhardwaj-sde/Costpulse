"""Unit tests for core constants."""

from costpulse.core.constants import ANOMALY_THRESHOLDS, DBU_RATES, VM_COSTS


def test_dbu_rates_exist():
    """Test that DBU rates are defined."""
    assert len(DBU_RATES) > 0
    assert "JOBS_COMPUTE" in DBU_RATES
    assert "SQL_COMPUTE_SERVERLESS" in DBU_RATES


def test_dbu_rates_positive():
    """Test that all DBU rates are positive."""
    for sku, rate in DBU_RATES.items():
        assert rate > 0, f"Rate for {sku} should be positive"


def test_vm_costs_exist():
    """Test that VM costs are defined for major cloud providers."""
    assert "AWS" in VM_COSTS
    assert "AZURE" in VM_COSTS
    assert "GCP" in VM_COSTS


def test_vm_costs_positive():
    """Test that all VM costs are positive."""
    for cloud, instances in VM_COSTS.items():
        for instance_type, cost in instances.items():
            assert cost > 0, f"Cost for {cloud}/{instance_type} should be positive"


def test_anomaly_thresholds_exist():
    """Test that anomaly thresholds are defined."""
    assert "cost_spike_percent" in ANOMALY_THRESHOLDS
    assert "idle_cluster_minutes" in ANOMALY_THRESHOLDS
    assert "query_cost_threshold" in ANOMALY_THRESHOLDS
