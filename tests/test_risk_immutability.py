"""Tests: alle Risk-Datenmodelle sind unveränderlich (frozen)."""

from __future__ import annotations

import dataclasses

import pytest

from models.risk import (
    OpenPosition,
    PositionSizing,
    RiskComponent,
    RiskLevel,
    RiskModelOutput,
    RiskReport,
    RiskResult,
)

FROZEN_SAMPLES = [
    OpenPosition("A", 1000.0),
    RiskComponent("volatility", 20.0, "reason"),
    RiskModelOutput(name="m", value=10.0),
    PositionSizing(),
    RiskResult(
        risk_id="risk:x",
        score_id="score:x",
        hypothesis_id="h",
        overall_risk=20.0,
        risk_level=RiskLevel.LOW,
        suggested_position_size=0.0,
        maximum_risk_pct=1.0,
        maximum_portfolio_exposure=10000.0,
        estimated_shares=0.0,
        estimated_order_value=0.0,
        estimated_slippage=0.0,
        estimated_commission=0.0,
        suggested_stop_distance=0.0,
        suggested_take_profit=0.0,
        suggested_risk_reward=2.0,
    ),
    RiskReport(),
]


@pytest.mark.parametrize("obj", FROZEN_SAMPLES, ids=lambda o: type(o).__name__)
def test_risk_models_are_frozen(obj: object) -> None:
    assert type(obj).__dataclass_params__.frozen is True
    first_field = dataclasses.fields(obj)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(obj, first_field, getattr(obj, first_field))
