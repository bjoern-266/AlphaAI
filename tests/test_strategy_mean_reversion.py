"""Tests für die Mean-Reversion-Strategie."""

from __future__ import annotations

from strategies.base import StrategyContext, StrategyDirection
from strategies.mean_reversion import MeanReversionStrategy
from tests.helpers import make_indicator_result, make_pattern_report, make_price_frame

_PARAMS = {"base_confidence": 0.55, "rsi_oversold": 30.0, "rsi_overbought": 70.0}


def _context(rsi: float, close: float, bollinger: dict[str, float]) -> StrategyContext:
    return StrategyContext(
        indicators=make_indicator_result(rsi=rsi, bollinger=bollinger),
        patterns=make_pattern_report(),
        data=make_price_frame([close]),
        symbol="TEST",
    )


def test_bullish_reversion() -> None:
    bands = {"upper": 120.0, "middle": 100.0, "lower": 90.0}
    evaluation = MeanReversionStrategy().evaluate(
        _context(25.0, close=88.0, bollinger=bands), _PARAMS
    )
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BULLISH


def test_bearish_reversion() -> None:
    bands = {"upper": 120.0, "middle": 100.0, "lower": 90.0}
    evaluation = MeanReversionStrategy().evaluate(
        _context(75.0, close=122.0, bollinger=bands), _PARAMS
    )
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BEARISH


def test_oversold_but_inside_band_no_hypothesis() -> None:
    bands = {"upper": 120.0, "middle": 100.0, "lower": 90.0}
    evaluation = MeanReversionStrategy().evaluate(
        _context(25.0, close=100.0, bollinger=bands), _PARAMS
    )
    assert evaluation.result is None


def test_neutral_rsi_no_hypothesis() -> None:
    bands = {"upper": 120.0, "middle": 100.0, "lower": 90.0}
    evaluation = MeanReversionStrategy().evaluate(
        _context(50.0, close=88.0, bollinger=bands), _PARAMS
    )
    assert evaluation.result is None


def test_missing_rsi_no_hypothesis() -> None:
    context = StrategyContext(
        indicators=make_indicator_result(bollinger={"upper": 1, "middle": 1, "lower": 1}),
        patterns=make_pattern_report(),
        data=make_price_frame([100.0]),
    )
    evaluation = MeanReversionStrategy().evaluate(context, _PARAMS)
    assert evaluation.result is None
    assert evaluation.warnings
