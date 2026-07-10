"""Tests für die Backtest-Registry."""

from __future__ import annotations

import pytest

from backtesting.base import BacktestContext, BacktestModelOutput, BaseBacktestModel
from core.exceptions import DuplicateRegistrationError, UnknownComponentError
from engines.backtest_registry import BacktestRegistry, build_default_registry


class _Dummy(BaseBacktestModel):
    name = "dummy_model"

    def compute(self, context, params):  # noqa: D102, ANN001
        return BacktestModelOutput(name=self.name)


def test_default_registry_has_four_models():
    registry = build_default_registry()
    assert len(registry) == 4


def test_default_registry_names():
    registry = build_default_registry()
    assert registry.names() == [
        "benchmark_model",
        "drawdown_model",
        "performance_model",
        "ratio_model",
    ]


def test_registry_contains():
    registry = build_default_registry()
    assert "performance_model" in registry
    assert "missing_model" not in registry


def test_registry_get_returns_model():
    registry = build_default_registry()
    model = registry.get("performance_model")
    assert model.name == "performance_model"


def test_registry_register_new():
    registry = BacktestRegistry()
    registry.register(_Dummy())
    assert "dummy_model" in registry
    assert len(registry) == 1


def test_registry_duplicate_raises():
    registry = BacktestRegistry()
    registry.register(_Dummy())
    with pytest.raises(DuplicateRegistrationError):
        registry.register(_Dummy())


def test_registry_unknown_raises():
    registry = BacktestRegistry()
    with pytest.raises(UnknownComponentError):
        registry.get("nope")


def test_registry_label_in_error():
    registry = BacktestRegistry()
    with pytest.raises(UnknownComponentError) as excinfo:
        registry.get("nope")
    assert "Backtest-Modell" in str(excinfo.value)


def test_every_default_model_is_base_subclass():
    registry = build_default_registry()
    for name in registry.names():
        assert isinstance(registry.get(name), BaseBacktestModel)


def test_models_compute_returns_output():
    from tests.helpers import make_simulated_trade

    context = BacktestContext(
        symbol="AAPL",
        timeframe="base",
        starting_capital=10000.0,
        trades=[make_simulated_trade()],
        equity_curve=[],
    )
    registry = build_default_registry()
    params = {"risk_free_rate": 0.0, "periods_per_year": 0}
    for name in registry.names():
        out = registry.get(name).compute(context, params)
        assert isinstance(out, BacktestModelOutput)
