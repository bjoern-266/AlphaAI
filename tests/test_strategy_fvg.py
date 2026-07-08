"""Tests für die FVG-Strategie."""

from __future__ import annotations

from patterns.base import PatternDirection
from strategies.base import StrategyContext, StrategyDirection
from strategies.fvg_strategy import FvgStrategy
from tests.helpers import (
    make_indicator_result,
    make_pattern_report,
    make_pattern_result,
    make_price_frame,
)

_PARAMS = {"base_confidence": 0.6, "require_fresh": True}


def _context(fvg_direction: PatternDirection, close: float, ema200: float, fresh: bool = True):
    patterns = make_pattern_report(
        [make_pattern_result("fvg", direction=fvg_direction, strength=42.0, fresh=fresh)]
    )
    return StrategyContext(
        indicators=make_indicator_result(ema={20: 1, 50: 1, 200: ema200}),
        patterns=patterns,
        data=make_price_frame([close]),
        symbol="TEST",
    )


def test_bullish_fvg_aligned_with_trend() -> None:
    evaluation = FvgStrategy().evaluate(
        _context(PatternDirection.BULLISH, close=110.0, ema200=100.0), _PARAMS
    )
    assert evaluation.result is not None
    result = evaluation.result
    assert result.direction is StrategyDirection.BULLISH
    assert result.matched_patterns == ["fvg"]
    assert result.matched_indicators == ["ema"]
    assert result.strength == 42.0
    assert "Fair Value Gap" in result.metadata["hypothesis"]


def test_bearish_fvg_aligned_with_trend() -> None:
    evaluation = FvgStrategy().evaluate(
        _context(PatternDirection.BEARISH, close=90.0, ema200=100.0), _PARAMS
    )
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BEARISH


def test_fvg_against_trend_no_hypothesis() -> None:
    evaluation = FvgStrategy().evaluate(
        _context(PatternDirection.BULLISH, close=90.0, ema200=100.0), _PARAMS
    )
    assert evaluation.result is None
    assert evaluation.warnings


def test_require_fresh_filters_mitigated() -> None:
    evaluation = FvgStrategy().evaluate(
        _context(PatternDirection.BULLISH, close=110.0, ema200=100.0, fresh=False), _PARAMS
    )
    assert evaluation.result is None
    assert evaluation.warnings


def test_fvg_without_trend_data_uses_pattern_direction() -> None:
    patterns = make_pattern_report([make_pattern_result("fvg", direction=PatternDirection.BULLISH)])
    context = StrategyContext(
        indicators=make_indicator_result(ema={20: 1, 50: 1, 200: 100.0}),
        patterns=patterns,
        data=None,
        symbol="TEST",
    )
    evaluation = FvgStrategy().evaluate(context, _PARAMS)
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BULLISH
