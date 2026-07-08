"""Tests für die Breakout-Strategie."""

from __future__ import annotations

from patterns.base import PatternDirection, PatternType
from strategies.base import StrategyContext, StrategyDirection
from strategies.breakout_strategy import BreakoutStrategy
from tests.helpers import (
    make_indicator_result,
    make_pattern_report,
    make_pattern_result,
    make_price_frame,
)

_PARAMS = {"base_confidence": 0.6, "rvol_min": 1.5}


def _context(bos_direction: PatternDirection, rvol: float) -> StrategyContext:
    patterns = make_pattern_report(
        [
            make_pattern_result(
                "bos",
                direction=bos_direction,
                strength=30.0,
                pattern_type=PatternType.STRUCTURE_BREAK,
                price_level=180.0,
            )
        ]
    )
    return StrategyContext(
        indicators=make_indicator_result(relative_volume=rvol),
        patterns=patterns,
        data=make_price_frame([100.0]),
        symbol="TEST",
    )


def test_bullish_breakout_confirmed() -> None:
    evaluation = BreakoutStrategy().evaluate(_context(PatternDirection.BULLISH, rvol=2.0), _PARAMS)
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BULLISH
    assert evaluation.result.matched_patterns == ["bos"]
    assert evaluation.result.strength == 30.0


def test_bearish_breakout_confirmed() -> None:
    evaluation = BreakoutStrategy().evaluate(_context(PatternDirection.BEARISH, rvol=2.0), _PARAMS)
    assert evaluation.result is not None
    assert evaluation.result.direction is StrategyDirection.BEARISH


def test_low_volume_no_hypothesis() -> None:
    evaluation = BreakoutStrategy().evaluate(_context(PatternDirection.BULLISH, rvol=1.0), _PARAMS)
    assert evaluation.result is None
    assert any("Volumen" in w for w in evaluation.warnings)


def test_no_bos_no_hypothesis() -> None:
    context = StrategyContext(
        indicators=make_indicator_result(relative_volume=2.0),
        patterns=make_pattern_report([]),  # kein BOS
        data=make_price_frame([100.0]),
    )
    evaluation = BreakoutStrategy().evaluate(context, _PARAMS)
    assert evaluation.result is None
    assert evaluation.warnings


def test_missing_rvol_no_hypothesis() -> None:
    patterns = make_pattern_report(
        [make_pattern_result("bos", pattern_type=PatternType.STRUCTURE_BREAK)]
    )
    context = StrategyContext(
        indicators=make_indicator_result(),  # kein relative_volume
        patterns=patterns,
        data=make_price_frame([100.0]),
    )
    evaluation = BreakoutStrategy().evaluate(context, _PARAMS)
    assert evaluation.result is None
    assert evaluation.warnings
