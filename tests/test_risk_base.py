"""Tests für die gemeinsamen Risk-Hilfsmittel (risk/base.py)."""

from __future__ import annotations

import pytest

from models.risk import RiskComponent
from risk.base import (
    RiskParameterError,
    atr_component,
    clamp_risk,
    compute_position_sizing,
    data_quality_component,
    news_component,
    require_bool,
    require_float,
    require_int,
    scaled_risk,
    validate_weights,
    weighted_sum,
)
from tests.helpers import make_risk_context

PS_PARAMS = {
    "atr_stop_multiplier": 2.0,
    "risk_reward": 2.0,
    "slippage_bps": 5.0,
    "commission_pct": 0.001,
    "min_commission": 1.0,
    "max_position_pct": 0.25,
    "max_portfolio_exposure_pct": 1.0,
}
COMPONENT_PARAMS = {"atr_low_pct": 1.0, "atr_high_pct": 6.0, "news_default": 50.0}


# --- scaled_risk / clamp_risk -------------------------------------------------


def test_scaled_risk_below_low_is_zero() -> None:
    assert scaled_risk(0.5, 1.0, 5.0) == 0.0


def test_scaled_risk_above_high_is_hundred() -> None:
    assert scaled_risk(9.0, 1.0, 5.0) == 100.0


def test_scaled_risk_midpoint() -> None:
    assert scaled_risk(3.0, 1.0, 5.0) == pytest.approx(50.0)


def test_scaled_risk_degenerate_range() -> None:
    assert scaled_risk(3.0, 5.0, 5.0) == 0.0


def test_clamp_risk_bounds() -> None:
    assert clamp_risk(-10.0) == 0.0
    assert clamp_risk(150.0) == 100.0
    assert clamp_risk(42.0) == 42.0


# --- validate_weights / weighted_sum -----------------------------------------


def test_validate_weights_ok() -> None:
    weights = validate_weights({"a": 0.5, "b": 0.5}, ("a", "b"), "m")
    assert weights == {"a": 0.5, "b": 0.5}


def test_validate_weights_sum_not_one() -> None:
    with pytest.raises(RiskParameterError, match="100"):
        validate_weights({"a": 0.5, "b": 0.4}, ("a", "b"), "m")


def test_validate_weights_missing() -> None:
    with pytest.raises(RiskParameterError, match="fehlende"):
        validate_weights({"a": 1.0}, ("a", "b"), "m")


def test_validate_weights_unknown() -> None:
    with pytest.raises(RiskParameterError, match="unbekannte"):
        validate_weights({"a": 0.5, "b": 0.5, "c": 0.0}, ("a", "b"), "m")


def test_validate_weights_out_of_range() -> None:
    with pytest.raises(RiskParameterError):
        validate_weights({"a": 1.5, "b": -0.5}, ("a", "b"), "m")


def test_weighted_sum() -> None:
    comps = {"a": RiskComponent("a", 80.0, ""), "b": RiskComponent("b", 40.0, "")}
    assert weighted_sum({"a": 0.5, "b": 0.5}, comps) == pytest.approx(60.0)


# --- require_* ---------------------------------------------------------------


def test_require_float_ok_and_errors() -> None:
    assert require_float({"x": 2}, "x", "m") == 2.0
    with pytest.raises(RiskParameterError):
        require_float({}, "x", "m")
    with pytest.raises(RiskParameterError):
        require_float({"x": -1}, "x", "m")
    with pytest.raises(RiskParameterError):
        require_float({"x": True}, "x", "m")


def test_require_int_ok_and_errors() -> None:
    assert require_int({"x": 5}, "x", "m") == 5
    with pytest.raises(RiskParameterError):
        require_int({"x": 0}, "x", "m")
    with pytest.raises(RiskParameterError):
        require_int({"x": 1.5}, "x", "m")


def test_require_bool_ok_and_errors() -> None:
    assert require_bool({"x": True}, "x", "m") is True
    with pytest.raises(RiskParameterError):
        require_bool({"x": 1}, "x", "m")


# --- compute_position_sizing -------------------------------------------------


def test_position_sizing_basic_relationships() -> None:
    context = make_risk_context(atr=2.0, capital=10000.0, fractional=True)
    ps = compute_position_sizing(context, PS_PARAMS)
    assert ps.maximum_risk_pct == pytest.approx(1.0)
    assert ps.suggested_stop_distance == pytest.approx(4.0)  # atr * 2
    assert ps.suggested_take_profit == pytest.approx(8.0)  # stop * rr
    assert ps.suggested_risk_reward == 2.0
    assert ps.estimated_shares > 0
    assert ps.estimated_order_value <= context.account.capital
    assert ps.estimated_commission >= PS_PARAMS["min_commission"]


def test_position_sizing_respects_position_cap() -> None:
    # per_position_cap = 25 % von 10000 = 2500; equal_weight = 10000/5 = 2000.
    context = make_risk_context(atr=2.0, capital=10000.0, max_open_positions=5)
    ps = compute_position_sizing(context, PS_PARAMS)
    assert ps.estimated_order_value <= 2000.0 + 1e-6


def test_position_sizing_non_fractional_is_integer() -> None:
    context = make_risk_context(atr=2.0, fractional=False)
    ps = compute_position_sizing(context, PS_PARAMS)
    assert ps.estimated_shares == float(int(ps.estimated_shares))


def test_position_sizing_missing_atr_yields_no_shares() -> None:
    context = make_risk_context(atr=None)
    ps = compute_position_sizing(context, PS_PARAMS)
    assert ps.estimated_shares == 0.0
    assert ps.maximum_risk_pct == pytest.approx(1.0)


def test_position_sizing_invalid_risk_reward() -> None:
    context = make_risk_context()
    params = {**PS_PARAMS, "risk_reward": 0.0}
    with pytest.raises(RiskParameterError, match="risk_reward"):
        compute_position_sizing(context, params)


def test_position_sizing_invalid_stop_multiplier() -> None:
    context = make_risk_context()
    params = {**PS_PARAMS, "atr_stop_multiplier": 0.0}
    with pytest.raises(RiskParameterError, match="atr_stop_multiplier"):
        compute_position_sizing(context, params)


# --- Basiskomponenten --------------------------------------------------------


def test_atr_component_scales_with_atr() -> None:
    comp = atr_component(make_risk_context(atr=3.0), COMPONENT_PARAMS)
    assert comp.name == "atr"
    assert 0.0 < comp.value < 100.0


def test_atr_component_neutral_without_atr() -> None:
    comp = atr_component(make_risk_context(atr=None), COMPONENT_PARAMS)
    assert comp.value == 50.0


def test_data_quality_component_inverts_quality() -> None:
    assert data_quality_component(make_risk_context(data_quality=100.0)).value == 0.0
    assert data_quality_component(make_risk_context(data_quality=40.0)).value == pytest.approx(60.0)


def test_news_component_is_prepared_neutral() -> None:
    comp = news_component(make_risk_context(), COMPONENT_PARAMS)
    assert comp.name == "news"
    assert comp.value == 50.0
    with pytest.raises(RiskParameterError):
        news_component(make_risk_context(), {})
