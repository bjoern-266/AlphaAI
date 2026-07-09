"""Tests für die Risk-Registry."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from engines.risk_registry import RiskRegistry, build_default_registry
from risk.base import BaseRiskModel, RiskContext, RiskModelOutput
from risk.volatility_risk import VolatilityRiskModel

EXPECTED = {
    "position_sizing",
    "volatility_risk",
    "liquidity_risk",
    "gap_risk",
    "market_risk",
    "correlation_risk",
    "portfolio_risk",
    "execution_risk",
}


class _DummyRiskModel(BaseRiskModel):
    name = "dummy"
    component = "volatility"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        return RiskModelOutput(name=self.name, value=0.0)


def test_default_registry_contains_all_models() -> None:
    registry = build_default_registry()
    assert len(registry) == 8
    assert set(registry.names()) == EXPECTED


def test_register_duplicate_raises() -> None:
    registry = build_default_registry()
    with pytest.raises(ValueError, match="bereits registriert"):
        registry.register(VolatilityRiskModel())


def test_get_unknown_raises() -> None:
    with pytest.raises(KeyError):
        build_default_registry().get("does_not_exist")


def test_register_new_model() -> None:
    registry = RiskRegistry()
    registry.register(_DummyRiskModel())
    assert "dummy" in registry
    assert registry.get("dummy").name == "dummy"
