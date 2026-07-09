"""Tests für die acht Risk-Modelle (risk/*.py)."""

from __future__ import annotations

import pytest

from models.risk import OpenPosition, PositionSizing
from risk.correlation_risk import CorrelationRiskModel
from risk.execution_risk import ExecutionRiskModel
from risk.gap_risk import GapRiskModel
from risk.liquidity_risk import LiquidityRiskModel
from risk.market_risk import MarketRiskModel
from risk.portfolio_risk import PortfolioRiskModel
from risk.position_sizing import PositionSizingModel
from risk.volatility_risk import VolatilityRiskModel
from tests.helpers import make_price_frame, make_risk_context

VOL_PARAMS = {"window": 20, "vol_low_pct": 1.0, "vol_high_pct": 5.0}
LIQ_PARAMS = {"window": 20, "min_dollar_volume": 100000.0, "good_dollar_volume": 5000000.0}
GAP_PARAMS = {"window": 20, "gap_low_pct": 0.2, "gap_high_pct": 3.0}
CORR_PARAMS = {"risk_per_correlated": 20.0}
PORT_PARAMS = {"max_exposure_ratio": 1.0}
EXEC_PARAMS = {"spread_bps": 5.0, "slippage_bps": 5.0, "cost_low_pct": 0.05, "cost_high_pct": 0.5}
PS_PARAMS = {
    "atr_stop_multiplier": 2.0,
    "risk_reward": 2.0,
    "slippage_bps": 5.0,
    "commission_pct": 0.001,
    "min_commission": 1.0,
    "max_position_pct": 0.25,
    "max_portfolio_exposure_pct": 1.0,
}


# --- Volatility --------------------------------------------------------------


def test_volatility_component_name() -> None:
    assert VolatilityRiskModel().component == "volatility"


def test_volatility_flat_prices_low_risk() -> None:
    flat = make_price_frame([100.0] * 40)
    out = VolatilityRiskModel().compute(make_risk_context(price_data=flat), VOL_PARAMS)
    assert out.value == 0.0


def test_volatility_high_swings_high_risk() -> None:
    swings = make_price_frame([100.0, 110.0] * 20)
    out = VolatilityRiskModel().compute(make_risk_context(price_data=swings), VOL_PARAMS)
    assert out.value == 100.0


def test_volatility_missing_data_neutral() -> None:
    out = VolatilityRiskModel().compute(make_risk_context(price_data=None, rows=1), VOL_PARAMS)
    assert out.value == 50.0


# --- Liquidity ---------------------------------------------------------------


def test_liquidity_component_name() -> None:
    assert LiquidityRiskModel().component == "liquidity"


def test_liquidity_high_volume_low_risk() -> None:
    out = LiquidityRiskModel().compute(make_risk_context(volume=1_000_000.0), LIQ_PARAMS)
    assert out.value == 0.0


def test_liquidity_low_volume_high_risk() -> None:
    out = LiquidityRiskModel().compute(make_risk_context(volume=500.0), LIQ_PARAMS)
    assert out.value == 100.0


# --- Gap ---------------------------------------------------------------------


def test_gap_component_name() -> None:
    assert GapRiskModel().component == "gap"


def test_gap_small_gaps_low_risk() -> None:
    out = GapRiskModel().compute(make_risk_context(), GAP_PARAMS)
    assert out.value < 20.0


def test_gap_large_gaps_high_risk() -> None:
    closes = [100.0] * 30
    opens = [105.0] * 30  # 5 % Overnight-Lücke
    frame = make_price_frame(closes, opens=opens)
    out = GapRiskModel().compute(make_risk_context(price_data=frame), GAP_PARAMS)
    assert out.value == 100.0


# --- Market ------------------------------------------------------------------


def test_market_component_name() -> None:
    assert MarketRiskModel().component == "market"


def test_market_risk_inverts_market_score() -> None:
    out = MarketRiskModel().compute(make_risk_context(market_score=60.0), {})
    assert out.value == pytest.approx(40.0)


def test_market_risk_weak_market_high_risk() -> None:
    out = MarketRiskModel().compute(make_risk_context(market_score=10.0), {})
    assert out.value == pytest.approx(90.0)


# --- Correlation -------------------------------------------------------------


def test_correlation_component_name() -> None:
    assert CorrelationRiskModel().component == "correlation"


def test_correlation_no_positions_zero() -> None:
    out = CorrelationRiskModel().compute(make_risk_context(open_positions=()), CORR_PARAMS)
    assert out.value == 0.0


def test_correlation_scales_with_positions() -> None:
    positions = (OpenPosition("A", 1000.0), OpenPosition("B", 1000.0))
    out = CorrelationRiskModel().compute(make_risk_context(open_positions=positions), CORR_PARAMS)
    assert out.value == pytest.approx(40.0)


def test_correlation_clamped_at_hundred() -> None:
    positions = tuple(OpenPosition(f"S{i}", 100.0) for i in range(10))
    out = CorrelationRiskModel().compute(make_risk_context(open_positions=positions), CORR_PARAMS)
    assert out.value == 100.0


# --- Portfolio ---------------------------------------------------------------


def test_portfolio_component_name() -> None:
    assert PortfolioRiskModel().component == "portfolio_exposure"


def test_portfolio_no_positions_zero() -> None:
    out = PortfolioRiskModel().compute(make_risk_context(open_positions=()), PORT_PARAMS)
    assert out.value == 0.0


def test_portfolio_half_exposure() -> None:
    positions = (OpenPosition("A", 5000.0),)
    out = PortfolioRiskModel().compute(
        make_risk_context(capital=10000.0, open_positions=positions), PORT_PARAMS
    )
    assert out.value == pytest.approx(50.0)


# --- Execution ---------------------------------------------------------------


def test_execution_component_is_spread() -> None:
    assert ExecutionRiskModel().component == "spread"


def test_execution_cost_scaled() -> None:
    out = ExecutionRiskModel().compute(make_risk_context(), EXEC_PARAMS)
    # cost_pct = (5 + 2*5)/100 = 0.15 -> scaled(0.15, 0.05, 0.5) ~ 22.2
    assert out.value == pytest.approx(22.222, abs=0.1)


# --- Position Sizing ---------------------------------------------------------


def test_position_sizing_no_component() -> None:
    assert PositionSizingModel().component == ""


def test_position_sizing_details_carry_sizing() -> None:
    out = PositionSizingModel().compute(make_risk_context(), PS_PARAMS)
    assert isinstance(out.details["sizing"], PositionSizing)
    assert out.value == pytest.approx(1.0)  # maximum_risk_pct


def test_position_sizing_warns_without_shares() -> None:
    out = PositionSizingModel().compute(make_risk_context(atr=None), PS_PARAMS)
    assert out.warnings
