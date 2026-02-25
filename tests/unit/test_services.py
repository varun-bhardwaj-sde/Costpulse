"""Tests for service layer business logic."""

import uuid
from datetime import datetime
from unittest.mock import MagicMock

from costpulse.services.anomaly_detection import AnomalyDetectionService
from costpulse.services.tag_compliance import DEFAULT_REQUIRED_TAGS, TagComplianceService


class TestAnomalyDetection:
    """Test the anomaly detection Z-score algorithm."""

    def test_zscore_detects_spike(self):
        service = AnomalyDetectionService.__new__(AnomalyDetectionService)
        values = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 103.0, 250.0]
        dates = [f"2026-02-{i+1:02d}" for i in range(len(values))]

        anomalies = service._find_zscore_anomalies(values, dates, "test", sensitivity=2.0)
        assert len(anomalies) > 0
        assert anomalies[0]["direction"] == "spike"
        assert anomalies[0]["value"] == 250.0

    def test_zscore_detects_drop(self):
        service = AnomalyDetectionService.__new__(AnomalyDetectionService)
        values = [100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 103.0, 10.0]
        dates = [f"2026-02-{i+1:02d}" for i in range(len(values))]

        anomalies = service._find_zscore_anomalies(values, dates, "test", sensitivity=2.0)
        assert len(anomalies) > 0
        assert anomalies[0]["direction"] == "drop"

    def test_zscore_no_anomaly_for_stable_data(self):
        service = AnomalyDetectionService.__new__(AnomalyDetectionService)
        values = [100.0, 101.0, 99.0, 100.5, 99.5, 100.0, 100.2, 99.8]
        dates = [f"2026-02-{i+1:02d}" for i in range(len(values))]

        anomalies = service._find_zscore_anomalies(values, dates, "test", sensitivity=2.0)
        assert len(anomalies) == 0

    def test_zscore_severity_levels(self):
        service = AnomalyDetectionService.__new__(AnomalyDetectionService)
        # Use slight variation to avoid std=0, then extreme spike
        values = [100.0, 101.0, 99.0, 100.5, 99.5, 100.2, 100.8, 500.0]
        dates = [f"2026-02-{i+1:02d}" for i in range(len(values))]

        anomalies = service._find_zscore_anomalies(values, dates, "test", sensitivity=2.0)
        assert len(anomalies) > 0
        assert anomalies[0]["severity"] == "critical"


class TestTagCompliance:
    def test_default_required_tags(self):
        assert "team" in DEFAULT_REQUIRED_TAGS
        assert "environment" in DEFAULT_REQUIRED_TAGS
        assert "project" in DEFAULT_REQUIRED_TAGS
        assert "cost_center" in DEFAULT_REQUIRED_TAGS

    def test_tag_recommendations_generated(self):
        service = TagComplianceService.__new__(TagComplianceService)
        cluster_compliance = {
            "total": 10,
            "compliant": 3,
            "non_compliant": 7,
            "compliance_pct": 30.0,
            "violations": [{"missing_tags": ["team", "team"]}],
        }
        cost_compliance = {
            "total": 5,
            "compliant": 2,
            "non_compliant": 3,
            "compliance_pct": 40.0,
            "violations": [{"missing_tags": ["environment"]}],
        }
        recs = service._generate_tag_recommendations(
            cluster_compliance, cost_compliance, DEFAULT_REQUIRED_TAGS
        )
        assert len(recs) > 0
        assert "Critical" in recs[0]


class TestCostAllocationRuleMatching:
    """Test allocation rule matching logic."""

    def _make_rule(self, rule_type, conditions, team_id=None):
        """Create a mock rule."""
        rule = MagicMock()
        rule.rule_type = rule_type
        rule.conditions = conditions
        rule.team_id = team_id or str(uuid.uuid4())
        return rule

    def test_tag_match_rule(self):
        from costpulse.services.cost_allocation import CostAllocationService

        service = CostAllocationService.__new__(CostAllocationService)

        record = MagicMock()
        record.tags = {"team": "data-eng", "environment": "prod"}
        record.user_email = None
        record.workspace_id = "ws-123"
        record.cluster_name = None
        record.sku_name = "JOBS_COMPUTE"

        rule = self._make_rule("tag_match", {"tag_key": "team", "tag_value": "data-eng"})
        assert service._rule_matches(record, rule) is True

    def test_user_match_rule(self):
        from costpulse.services.cost_allocation import CostAllocationService

        service = CostAllocationService.__new__(CostAllocationService)

        record = MagicMock()
        record.tags = {}
        record.user_email = "alice@company.com"
        record.workspace_id = "ws-123"
        record.cluster_name = None
        record.sku_name = "JOBS_COMPUTE"

        rule = self._make_rule("user_match", {"emails": ["alice@company.com", "bob@company.com"]})
        assert service._rule_matches(record, rule) is True

    def test_workspace_match_rule(self):
        from costpulse.services.cost_allocation import CostAllocationService

        service = CostAllocationService.__new__(CostAllocationService)

        record = MagicMock()
        record.tags = {}
        record.user_email = None
        record.workspace_id = "ws-prod-001"
        record.cluster_name = None
        record.sku_name = "ALL_PURPOSE_COMPUTE"

        rule = self._make_rule("workspace_match", {"workspace_ids": ["ws-prod-001", "ws-prod-002"]})
        assert service._rule_matches(record, rule) is True

    def test_cluster_name_pattern_match(self):
        from costpulse.services.cost_allocation import CostAllocationService

        service = CostAllocationService.__new__(CostAllocationService)

        record = MagicMock()
        record.tags = {}
        record.user_email = None
        record.workspace_id = "ws-123"
        record.cluster_name = "ml-training-gpu-01"
        record.sku_name = "ALL_PURPOSE_COMPUTE"

        rule = self._make_rule("cluster_match", {"cluster_name_patterns": ["ml-.*", "ai-.*"]})
        assert service._rule_matches(record, rule) is True

    def test_no_match(self):
        from costpulse.services.cost_allocation import CostAllocationService

        service = CostAllocationService.__new__(CostAllocationService)

        record = MagicMock()
        record.tags = {"team": "analytics"}
        record.user_email = None
        record.workspace_id = "ws-123"
        record.cluster_name = None
        record.sku_name = "JOBS_COMPUTE"

        rule = self._make_rule("tag_match", {"tag_key": "team", "tag_value": "data-eng"})
        assert service._rule_matches(record, rule) is False


class TestForecastLinearRegression:
    """Test the linear forecast fallback."""

    def test_linear_forecast_positive_trend(self):
        from costpulse.services.forecast_service import ForecastService

        service = ForecastService.__new__(ForecastService)
        historical = [
            {"date": datetime(2026, 1, i + 1), "cost": 1000 + i * 10, "dbu": 100} for i in range(30)
        ]
        forecasts = service._linear_forecast(historical, horizon_days=7)

        assert len(forecasts) == 7
        assert all(f["predicted_cost"] > 0 for f in forecasts)
        assert all(f["lower_bound"] <= f["predicted_cost"] <= f["upper_bound"] for f in forecasts)
        assert all(f["model"] == "linear" for f in forecasts)

    def test_linear_forecast_stable_data(self):
        from costpulse.services.forecast_service import ForecastService

        service = ForecastService.__new__(ForecastService)
        historical = [
            {"date": datetime(2026, 1, i + 1), "cost": 1000.0, "dbu": 100} for i in range(30)
        ]
        forecasts = service._linear_forecast(historical, horizon_days=7)

        assert len(forecasts) == 7
        for f in forecasts:
            assert abs(f["predicted_cost"] - 1000) < 100


class TestRecommendationHourlyCost:
    """Test cluster cost estimation using mock objects."""

    def test_estimate_hourly_cost(self):
        from costpulse.services.recommendation_service import RecommendationService

        service = RecommendationService.__new__(RecommendationService)

        cluster = MagicMock()
        cluster.num_workers = 4
        cluster.node_type = "i3.xlarge"
        cluster.photon_enabled = False

        cost = service._estimate_hourly_cost(cluster)
        assert cost > 0

    def test_photon_increases_cost(self):
        from costpulse.services.recommendation_service import RecommendationService

        service = RecommendationService.__new__(RecommendationService)

        cluster_no_photon = MagicMock()
        cluster_no_photon.num_workers = 4
        cluster_no_photon.node_type = "i3.xlarge"
        cluster_no_photon.photon_enabled = False

        cluster_photon = MagicMock()
        cluster_photon.num_workers = 4
        cluster_photon.node_type = "i3.xlarge"
        cluster_photon.photon_enabled = True

        cost_no = service._estimate_hourly_cost(cluster_no_photon)
        cost_photon = service._estimate_hourly_cost(cluster_photon)
        assert cost_photon > cost_no
