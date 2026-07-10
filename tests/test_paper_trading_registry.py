"""Tests für die Paper-Trading-Registry."""

from __future__ import annotations

import pytest

from core.exceptions import DuplicateRegistrationError, UnknownComponentError
from engines.paper_trading_registry import PaperTradingRegistry, build_default_registry
from paper_trading.base import (
    BasePaperTradingModel,
    PaperTradingContext,
    PaperTradingModelOutput,
)


class _Dummy(BasePaperTradingModel):
    name = "dummy_model"

    def compute(self, context, params):  # noqa: D102, ANN001
        return PaperTradingModelOutput(name=self.name)


def _context():
    return PaperTradingContext(
        symbol="AAPL",
        timeframe="base",
        starting_capital=10000.0,
        current_equity=10000.0,
        positions=[],
        trades=[],
        equity_curve=[],
    )


def test_default_registry_has_two_models():
    assert len(build_default_registry()) == 2


def test_default_registry_names():
    assert build_default_registry().names() == ["performance_model", "statistics_model"]


def test_registry_contains():
    registry = build_default_registry()
    assert "statistics_model" in registry
    assert "missing" not in registry


def test_registry_get():
    assert build_default_registry().get("performance_model").name == "performance_model"


def test_register_new():
    registry = PaperTradingRegistry()
    registry.register(_Dummy())
    assert "dummy_model" in registry


def test_duplicate_raises():
    registry = PaperTradingRegistry()
    registry.register(_Dummy())
    with pytest.raises(DuplicateRegistrationError):
        registry.register(_Dummy())


def test_unknown_raises():
    with pytest.raises(UnknownComponentError):
        PaperTradingRegistry().get("nope")


def test_label_in_error():
    with pytest.raises(UnknownComponentError) as excinfo:
        PaperTradingRegistry().get("nope")
    assert "Paper-Trading-Modell" in str(excinfo.value)


def test_default_models_are_base_subclasses():
    registry = build_default_registry()
    for name in registry.names():
        assert isinstance(registry.get(name), BasePaperTradingModel)


def test_models_compute_returns_output():
    registry = build_default_registry()
    for name in registry.names():
        out = registry.get(name).compute(_context(), {})
        assert isinstance(out, PaperTradingModelOutput)
