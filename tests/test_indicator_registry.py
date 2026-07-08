"""Tests für die Indicator-Registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from engines.indicator_registry import IndicatorRegistry, build_default_registry
from indicators.base import BaseIndicator, IndicatorOutput
from indicators.ema import EmaIndicator

EXPECTED = {
    "ema",
    "rsi",
    "atr",
    "vwap",
    "macd",
    "relative_volume",
    "adx",
    "bollinger",
    "stochastic",
    "obv",
    "volume_profile",
}


class _DummyIndicator(BaseIndicator):
    name = "dummy"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        return 1

    def compute(self, data: Any, params: Mapping[str, Any]) -> IndicatorOutput:
        return IndicatorOutput(name=self.name)


def test_default_registry_contains_all_indicators() -> None:
    registry = build_default_registry()
    assert len(registry) == 11
    assert set(registry.names()) == EXPECTED


def test_register_duplicate_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(EmaIndicator())


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        build_default_registry().get("does_not_exist")


def test_register_new_indicator() -> None:
    registry = IndicatorRegistry()
    registry.register(_DummyIndicator())
    assert "dummy" in registry
    assert registry.get("dummy").name == "dummy"
