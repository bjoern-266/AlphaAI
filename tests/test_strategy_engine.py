"""Tests für die StrategyEngine (Kombination, Validierung, Cache)."""

from __future__ import annotations

from engines.strategy_cache import StrategyCache
from engines.strategy_engine import StrategyEngine, StrategyRules, load_strategy_rules
from patterns.base import PatternDirection, PatternType
from strategies.base import StrategyDirection
from tests.helpers import (
    make_indicator_result,
    make_pattern_report,
    make_pattern_result,
    make_price_frame,
)


def _full_indicators(timeframe: str = "base"):
    return make_indicator_result(
        ema={20: 110, 50: 105, 200: 100},
        adx=30.0,
        rsi=60.0,
        macd={"macd": 1.0, "signal": 0.0, "histogram": 0.5},
        relative_volume=2.0,
        bollinger={"upper": 120.0, "middle": 100.0, "lower": 90.0},
        timeframe=timeframe,
    )


def _full_patterns(timeframe: str = "base"):
    return make_pattern_report(
        [
            make_pattern_result("fvg", direction=PatternDirection.BULLISH, fresh=True),
            make_pattern_result(
                "bos", direction=PatternDirection.BULLISH, pattern_type=PatternType.STRUCTURE_BREAK
            ),
        ],
        timeframe=timeframe,
    )


def _engine(cache: StrategyCache | None = None) -> StrategyEngine:
    return StrategyEngine(load_strategy_rules(), cache=cache)


def test_engine_produces_bullish_hypotheses() -> None:
    report = _engine().evaluate(
        _full_indicators(), _full_patterns(), data=make_price_frame([110.0]), symbol="TEST"
    )
    assert report.valid is True
    names = {r.strategy_name for r in report.results}
    assert {"fvg_strategy", "trend_following", "momentum_strategy", "breakout_strategy"} <= names
    assert all(r.direction is StrategyDirection.BULLISH for r in report.results)
    assert report.metadata["bullish"] == report.hypothesis_count


def test_engine_records_calculation_time() -> None:
    report = _engine().evaluate(
        _full_indicators(), _full_patterns(), data=make_price_frame([110.0])
    )
    assert report.calculation_time >= 0.0


def test_engine_skips_on_missing_indicators_and_patterns() -> None:
    report = _engine().evaluate(
        make_indicator_result(ema={20: 110, 50: 105, 200: 100}),
        make_pattern_report([]),
        data=make_price_frame([110.0]),
    )
    assert report.hypothesis_count == 0
    assert any("fehlende Indikatoren" in w for w in report.warnings)
    assert any("fehlende Muster" in w for w in report.warnings)


def test_engine_invalid_indicators_marks_report_invalid() -> None:
    report = _engine().evaluate(
        make_indicator_result(ema={20: 1, 50: 1, 200: 1}, valid=False),
        _full_patterns(),
        data=make_price_frame([110.0]),
    )
    assert report.valid is False
    assert any("Indikatordaten" in w for w in report.warnings)


def test_engine_invalid_patterns_warns() -> None:
    report = _engine().evaluate(
        _full_indicators(),
        make_pattern_report([], valid=False),
        data=make_price_frame([110.0]),
    )
    assert report.valid is False
    assert any("Musterdaten" in w for w in report.warnings)


def test_engine_inconsistent_timeframe_warns() -> None:
    report = _engine().evaluate(
        _full_indicators(timeframe="1d"),
        _full_patterns(timeframe="1h"),
        data=make_price_frame([110.0]),
    )
    assert any("Inkonsistente Ergebnisse" in w for w in report.warnings)


def test_engine_uses_cache() -> None:
    cache = StrategyCache()
    engine = _engine(cache=cache)
    ind = _full_indicators()
    pat = _full_patterns()
    frame = make_price_frame([110.0])
    engine.evaluate(ind, pat, data=frame, symbol="X")
    engine.evaluate(ind, pat, data=frame, symbol="X")
    assert cache.hits == 1
    assert cache.misses == 1


def test_engine_disabled_strategy_is_skipped() -> None:
    rules = StrategyRules(strategies={"fvg_strategy": {"enabled": False}}, version=1)
    report = StrategyEngine(rules).evaluate(
        _full_indicators(), _full_patterns(), data=make_price_frame([110.0])
    )
    assert report.hypothesis_count == 0
    assert not any("nicht registriert" in w for w in report.warnings)


def test_engine_parameter_error_marks_invalid() -> None:
    rules = StrategyRules(strategies={"fvg_strategy": {"enabled": True}}, version=1)
    report = StrategyEngine(rules).evaluate(
        make_indicator_result(ema={20: 1, 50: 1, 200: 100.0}),
        make_pattern_report([make_pattern_result("fvg", direction=PatternDirection.BULLISH)]),
        data=make_price_frame([110.0]),
    )
    assert report.valid is False
    assert any("base_confidence" in w for w in report.warnings)


def test_engine_metadata_lists_hypotheses() -> None:
    report = _engine().evaluate(
        _full_indicators(), _full_patterns(), data=make_price_frame([110.0])
    )
    assert isinstance(report.metadata["hypotheses"], list)
    assert report.metadata["hypotheses"]


def test_engine_produces_bearish_hypotheses() -> None:
    indicators = make_indicator_result(
        ema={20: 90, 50: 95, 200: 100},
        adx=30.0,
        rsi=40.0,
        macd={"macd": -1.0, "signal": 0.0, "histogram": -0.5},
        relative_volume=2.0,
        bollinger={"upper": 120.0, "middle": 100.0, "lower": 90.0},
    )
    patterns = make_pattern_report(
        [
            make_pattern_result("fvg", direction=PatternDirection.BEARISH, fresh=True),
            make_pattern_result(
                "bos", direction=PatternDirection.BEARISH, pattern_type=PatternType.STRUCTURE_BREAK
            ),
        ]
    )
    report = _engine().evaluate(indicators, patterns, data=make_price_frame([90.0]), symbol="TEST")
    assert report.hypothesis_count >= 3
    assert all(r.direction is StrategyDirection.BEARISH for r in report.results)
    assert report.metadata["bearish"] == report.hypothesis_count
