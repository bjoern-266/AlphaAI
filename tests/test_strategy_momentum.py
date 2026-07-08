"""Tests für die Momentum-Strategie."""

from __future__ import annotations

from strategies.base import StrategyContext, StrategyDirection
from strategies.momentum_strategy import MomentumStrategy
from tests.helpers import make_indicator_result, make_pattern_report, make_price_frame

_PARAMS = {"base_confidence": 0.6, "rsi_bull": 55.0, "rsi_bear": 45.0}


def _context(rsi: float, histogram: float) -> StrategyContext:
    return StrategyContext(
        indicators=make_indicator_result(
            rsi=rsi, macd={"macd": 0.0, "signal": 0.0, "histogram": histogram}
        ),
        patterns=make_pattern_report(),
        data=make_price_frame([100.0]),
        symbol="TEST",
    )


def test_bullish_momentum() -> None:
    evaluation = MomentumStrategy().evaluate(_context(rsi=60.0, histogram=0.5), _PARAMS)
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BULLISH


def test_bearish_momentum() -> None:
    evaluation = MomentumStrategy().evaluate(_context(rsi=40.0, histogram=-0.5), _PARAMS)
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BEARISH


def test_conflicting_signals_no_hypothesis() -> None:
    evaluation = MomentumStrategy().evaluate(_context(rsi=60.0, histogram=-0.5), _PARAMS)
    assert evaluation.result is None
    assert evaluation.warnings


def test_neutral_rsi_no_hypothesis() -> None:
    evaluation = MomentumStrategy().evaluate(_context(rsi=50.0, histogram=0.5), _PARAMS)
    assert evaluation.result is None


def test_missing_macd_no_hypothesis() -> None:
    context = StrategyContext(
        indicators=make_indicator_result(rsi=60.0),  # kein MACD
        patterns=make_pattern_report(),
        data=make_price_frame([100.0]),
    )
    evaluation = MomentumStrategy().evaluate(context, _PARAMS)
    assert evaluation.result is None
    assert evaluation.warnings
