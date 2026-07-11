"""Tests für die Analytics-Registry."""

from __future__ import annotations

import pytest

from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel
from core.exceptions import DuplicateRegistrationError, UnknownComponentError
from engines.analytics_registry import AnalyticsRegistry, build_default_registry
from tests.helpers import make_analytics_context

_EXPECTED = {
    "trade_statistics",
    "performance_analyzer",
    "pattern_analysis",
    "strategy_analysis",
    "recommendation_analysis",
    "risk_analysis",
    "market_analysis",
    "time_analysis",
    "journal_analysis",
    "summary_analysis",
}


class _Dummy(BaseAnalyticsModel):
    name = "dummy_model"

    def compute(self, context, params):  # noqa: D102, ANN001
        return AnalyticsModelOutput(name=self.name)


def test_default_registry_has_ten_models():
    assert len(build_default_registry()) == 10


def test_default_registry_names():
    assert set(build_default_registry().names()) == _EXPECTED


def test_registry_contains():
    registry = build_default_registry()
    assert "trade_statistics" in registry
    assert "missing" not in registry


def test_registry_get():
    assert build_default_registry().get("risk_analysis").name == "risk_analysis"


def test_register_new():
    registry = AnalyticsRegistry()
    registry.register(_Dummy())
    assert "dummy_model" in registry


def test_duplicate_raises():
    registry = AnalyticsRegistry()
    registry.register(_Dummy())
    with pytest.raises(DuplicateRegistrationError):
        registry.register(_Dummy())


def test_unknown_raises():
    with pytest.raises(UnknownComponentError):
        AnalyticsRegistry().get("nope")


def test_label_in_error():
    with pytest.raises(UnknownComponentError) as excinfo:
        AnalyticsRegistry().get("nope")
    assert "Analysemodell" in str(excinfo.value)


def test_all_models_are_base_subclasses():
    registry = build_default_registry()
    for name in registry.names():
        assert isinstance(registry.get(name), BaseAnalyticsModel)


def test_all_models_compute_independently():
    registry = build_default_registry()
    ctx: AnalyticsContext = make_analytics_context()
    for name in registry.names():
        out = registry.get(name).compute(ctx, {})
        assert isinstance(out, AnalyticsModelOutput)
