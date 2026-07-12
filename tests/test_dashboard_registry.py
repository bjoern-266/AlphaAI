"""Tests der Widget-Registry (einzige Stelle zum Registrieren von Widgets)."""

from __future__ import annotations

import pytest

from core.exceptions import AlphaAIError
from dashboard.widget_registry import WidgetRegistry, build_default_registry
from dashboard.widgets.base import BaseWidget
from dashboard.widgets.overview import OverviewKpisWidget
from models.dashboard import KIND_TEXT, WidgetSpec

# Alle 26 Standard-Widgets (Router referenziert genau diese IDs).
_EXPECTED = {
    "overview_kpis",
    "system_status",
    "recommendation_feed",
    "watchlist",
    "live_reasons",
    "portfolio_kpis",
    "portfolio_equity",
    "backtest_kpis",
    "backtest_equity",
    "backtest_trades",
    "analytics_long_short",
    "analytics_strategy",
    "analytics_pattern",
    "analytics_risk",
    "analytics_recommendation",
    "analytics_market",
    "analytics_time",
    "analytics_journal",
    "performance_equity",
    "performance_drawdown",
    "performance_profit_distribution",
    "performance_holding_time",
    "performance_returns",
    "journal_table",
    "recommendations_table",
    "mi_top_opportunities",
    "mi_ranking",
    "mi_heatmap",
    "mi_explanation",
    "mi_statistics",
    "settings_panel",
}


def test_default_registry_has_all_widgets():
    registry = build_default_registry()
    assert set(registry.names()) == _EXPECTED


def test_default_registry_count():
    assert len(build_default_registry()) == 31


def test_registry_contains():
    registry = build_default_registry()
    assert "overview_kpis" in registry
    assert "does_not_exist" not in registry


def test_registry_get_returns_widget():
    registry = build_default_registry()
    widget = registry.get("overview_kpis")
    assert isinstance(widget, OverviewKpisWidget)


def test_registry_get_unknown_raises():
    registry = build_default_registry()
    with pytest.raises(AlphaAIError):
        registry.get("missing")


def test_custom_widget_registration_without_engine_change():
    class CustomWidget(BaseWidget):
        name = "custom_demo"
        title = "Demo"

        def build(self, context):  # noqa: ANN001, D102
            return WidgetSpec(widget_id=self.name, title=self.title, kind=KIND_TEXT)

    registry = WidgetRegistry()
    registry.register(CustomWidget())
    assert "custom_demo" in registry


def test_registry_names_are_unique():
    names = build_default_registry().names()
    assert len(names) == len(set(names))


def test_registered_widget_id_matches_name():
    registry = build_default_registry()
    for name in registry.names():
        assert registry.get(name).name == name
