"""Tests für die Strategy-Registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from engines.strategy_registry import StrategyRegistry, build_default_registry
from strategies.base import BaseStrategy, StrategyContext, StrategyEvaluation
from strategies.fvg_strategy import FvgStrategy

EXPECTED = {
    "fvg_strategy",
    "trend_following",
    "momentum_strategy",
    "breakout_strategy",
    "mean_reversion",
}


class _DummyStrategy(BaseStrategy):
    name = "dummy"

    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        return StrategyEvaluation()


def test_default_registry_contains_all_strategies() -> None:
    registry = build_default_registry()
    assert len(registry) == 5
    assert set(registry.names()) == EXPECTED


def test_each_strategy_has_metadata() -> None:
    registry = build_default_registry()
    for name in registry.names():
        strategy = registry.get(name)
        assert strategy.name == name
        assert strategy.description
        assert strategy.version
        # Anforderungen sind Tupel (können leer sein).
        assert isinstance(strategy.pattern_requirements, tuple)
        assert isinstance(strategy.indicator_requirements, tuple)


def test_register_duplicate_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(FvgStrategy())


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        build_default_registry().get("does_not_exist")


def test_register_new_strategy() -> None:
    registry = StrategyRegistry()
    registry.register(_DummyStrategy())
    assert "dummy" in registry
    assert registry.get("dummy").name == "dummy"
