"""Tests für die Pattern-Registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from engines.pattern_registry import PatternRegistry, build_default_registry
from patterns.base import BasePattern, PatternDetection
from patterns.fvg import FvgPattern

EXPECTED = {
    "fvg",
    "bos",
    "choch",
    "equal_highs",
    "equal_lows",
    "liquidity_sweep",
    "market_structure",
    "trend_structure",
    "order_block",
    "breaker_block",
    "mitigation_block",
}


class _DummyPattern(BasePattern):
    name = "dummy"

    def min_candles(self, params: Mapping[str, Any]) -> int:
        return 1

    def detect(self, data: Any, params: Mapping[str, Any]) -> PatternDetection:
        return PatternDetection()


def test_default_registry_contains_all_patterns() -> None:
    registry = build_default_registry()
    assert len(registry) == 11
    assert set(registry.names()) == EXPECTED


def test_eight_implemented_three_prepared() -> None:
    registry = build_default_registry()
    implemented = [n for n in registry.names() if registry.get(n).implemented]
    prepared = [n for n in registry.names() if not registry.get(n).implemented]
    assert len(implemented) == 8
    assert set(prepared) == {"order_block", "breaker_block", "mitigation_block"}


def test_register_duplicate_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(FvgPattern())


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        build_default_registry().get("does_not_exist")


def test_register_new_pattern() -> None:
    registry = PatternRegistry()
    registry.register(_DummyPattern())
    assert "dummy" in registry
    assert registry.get("dummy").name == "dummy"
