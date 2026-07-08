"""Tests für die Trend-Following-Strategie."""

from __future__ import annotations

from strategies.base import StrategyContext, StrategyDirection
from strategies.trend_following import TrendFollowingStrategy
from tests.helpers import make_indicator_result, make_pattern_report, make_price_frame

_PARAMS = {"base_confidence": 0.65, "adx_min": 20.0}


def _context(ema: dict[int, float], adx: float) -> StrategyContext:
    return StrategyContext(
        indicators=make_indicator_result(ema=ema, adx=adx),
        patterns=make_pattern_report(),
        data=make_price_frame([100.0]),
        symbol="TEST",
    )


def test_bullish_trend() -> None:
    evaluation = TrendFollowingStrategy().evaluate(
        _context({20: 110, 50: 105, 200: 100}, adx=30.0), _PARAMS
    )
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BULLISH
    assert evaluation.result.strength == 30.0
    assert evaluation.result.matched_indicators == ["ema", "adx"]


def test_bearish_trend() -> None:
    evaluation = TrendFollowingStrategy().evaluate(
        _context({20: 90, 50: 95, 200: 100}, adx=30.0), _PARAMS
    )
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BEARISH


def test_weak_adx_no_hypothesis() -> None:
    evaluation = TrendFollowingStrategy().evaluate(
        _context({20: 110, 50: 105, 200: 100}, adx=10.0), _PARAMS
    )
    assert evaluation.result is None
    assert any("ADX" in w for w in evaluation.warnings)


def test_no_fan_no_hypothesis() -> None:
    evaluation = TrendFollowingStrategy().evaluate(
        _context({20: 100, 50: 110, 200: 105}, adx=30.0), _PARAMS
    )
    assert evaluation.result is None


def test_missing_ema_no_hypothesis() -> None:
    context = StrategyContext(
        indicators=make_indicator_result(adx=30.0),  # kein EMA
        patterns=make_pattern_report(),
        data=make_price_frame([100.0]),
    )
    evaluation = TrendFollowingStrategy().evaluate(context, _PARAMS)
    assert evaluation.result is None
    assert evaluation.warnings
