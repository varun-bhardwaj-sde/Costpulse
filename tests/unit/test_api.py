"""Tests for API endpoint schemas and routing."""

import pytest
from costpulse.api.main import app


class TestAppConfiguration:
    def test_app_title(self):
        assert app.title == "CostPulse FinOps Platform"

    def test_app_version(self):
        assert app.version == "0.2.0"

    def test_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert "/api/v1/health" in route_paths

    def test_cors_middleware(self):
        middlewares = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middlewares

    def test_dashboard_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/dashboard" in p for p in route_paths)

    def test_costs_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/costs" in p for p in route_paths)

    def test_teams_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/teams" in p for p in route_paths)

    def test_alerts_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/alerts" in p for p in route_paths)

    def test_recommendations_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/recommendations" in p for p in route_paths)

    def test_forecasts_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/forecasts" in p for p in route_paths)

    def test_reports_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/reports" in p for p in route_paths)

    def test_clusters_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/clusters" in p for p in route_paths)

    def test_tags_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/tags" in p for p in route_paths)

    def test_workspaces_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/workspaces" in p for p in route_paths)

    def test_allocations_routes_registered(self):
        route_paths = [route.path for route in app.routes]
        assert any("/api/v1/allocations" in p for p in route_paths)
