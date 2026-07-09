"""Tests für gemeinsame Score-Hilfsmittel (Validierung, Komponenten)."""

from __future__ import annotations

import pytest

from scores.base import (
    COMPONENT_NAMES,
    ScoreParameterError,
    compute_components,
    consensus_fraction,
    validate_weights,
    weighted_sum,
)
from strategies.base import StrategyDirection
from tests.helpers import (
    make_components,
    make_indicator_result,
    make_pattern_report,
    make_pattern_result,
    make_strategy_result,
)

WEIGHTS8 = {
    "trend": 0.2,
    "momentum": 0.2,
    "pattern_strength": 0.15,
    "pattern_confidence": 0.1,
    "indicator_quality": 0.1,
    "market_context": 0.1,
    "volume_quality": 0.075,
    "data_quality": 0.075,
}


def test_validate_weights_ok() -> None:
    weights = validate_weights(WEIGHTS8, COMPONENT_NAMES, "m")
    assert set(weights) == set(COMPONENT_NAMES)
    assert abs(sum(weights.values()) - 1.0) < 1e-9


def test_validate_weights_missing_component() -> None:
    partial = {k: v for k, v in WEIGHTS8.items() if k != "trend"}
    with pytest.raises(ScoreParameterError, match="fehlende"):
        validate_weights(partial, COMPONENT_NAMES, "m")


def test_validate_weights_unknown_key() -> None:
    extra = {**WEIGHTS8, "extra": 0.0}
    with pytest.raises(ScoreParameterError, match="unbekannte"):
        validate_weights(extra, COMPONENT_NAMES, "m")


def test_validate_weights_out_of_range() -> None:
    bad = {**WEIGHTS8, "trend": 1.5, "momentum": -0.3}
    with pytest.raises(ScoreParameterError, match="ungültiges Gewicht"):
        validate_weights(bad, COMPONENT_NAMES, "m")


def test_validate_weights_not_hundred_percent() -> None:
    bad = {**WEIGHTS8, "trend": 0.5}  # Summe > 1.0
    with pytest.raises(ScoreParameterError, match="100"):
        validate_weights(bad, COMPONENT_NAMES, "m")


def test_weighted_sum() -> None:
    components = make_components(trend=100.0, momentum=0.0)
    result = weighted_sum({"trend": 0.5, "momentum": 0.5}, components)
    assert result == 50.0


def test_consensus_fraction() -> None:
    target = make_strategy_result(direction=StrategyDirection.BULLISH)
    others = [
        make_strategy_result(direction=StrategyDirection.BULLISH),
        make_strategy_result(direction=StrategyDirection.BEARISH),
    ]
    assert consensus_fraction(target, [target, *others]) == pytest.approx(2 / 3)
    assert consensus_fraction(target, []) == 0.0


def test_components_are_complete() -> None:
    sr = make_strategy_result()
    components = compute_components(sr, make_indicator_result(), make_pattern_report())
    assert set(components) == set(COMPONENT_NAMES)
    assert all(0.0 <= c.value <= 100.0 for c in components.values())


def test_component_trend_aligned() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    ind = make_indicator_result(ema={20: 110, 50: 105, 200: 100}, adx=40.0)
    components = compute_components(sr, ind, make_pattern_report())
    assert components["trend"].value == pytest.approx(40.0)


def test_component_trend_not_aligned_is_halved() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BEARISH)
    ind = make_indicator_result(ema={20: 110, 50: 105, 200: 100}, adx=40.0)
    components = compute_components(sr, ind, make_pattern_report())
    assert components["trend"].value == pytest.approx(20.0)


def test_component_momentum_aligned() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    ind = make_indicator_result(rsi=70.0, macd={"macd": 1, "signal": 0, "histogram": 0.5})
    components = compute_components(sr, ind, make_pattern_report())
    assert components["momentum"].value == pytest.approx(40.0)


def test_component_pattern_strength_average() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    patterns = make_pattern_report(
        [make_pattern_result("fvg", strength=80.0), make_pattern_result("bos", strength=60.0)]
    )
    components = compute_components(sr, make_indicator_result(), patterns)
    assert components["pattern_strength"].value == pytest.approx(70.0)


def test_component_volume_quality_scales() -> None:
    sr = make_strategy_result()
    ind = make_indicator_result(relative_volume=2.0)
    components = compute_components(sr, ind, make_pattern_report())
    assert components["volume_quality"].value == pytest.approx(100.0)


def test_component_data_quality_penalises_invalid() -> None:
    sr = make_strategy_result()
    ind = make_indicator_result(valid=False)
    components = compute_components(sr, ind, make_pattern_report(valid=False))
    assert components["data_quality"].value < 100.0


def test_component_momentum_not_aligned_is_halved() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BEARISH)
    ind = make_indicator_result(rsi=70.0, macd={"macd": 1, "signal": 0, "histogram": 0.5})
    components = compute_components(sr, ind, make_pattern_report())
    assert components["momentum"].value == pytest.approx(20.0)


def test_component_indicator_quality_partial() -> None:
    sr = make_strategy_result()
    ind = make_indicator_result(ema={20: 1, 50: 1, 200: 1}, rsi=50.0)  # 2 von 11
    components = compute_components(sr, ind, make_pattern_report())
    assert 0.0 < components["indicator_quality"].value < 50.0


def test_component_market_context_aligned() -> None:
    from patterns.base import PatternDirection, PatternType

    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    patterns = make_pattern_report(
        [
            make_pattern_result(
                "market_structure",
                direction=PatternDirection.BULLISH,
                pattern_type=PatternType.MARKET_STRUCTURE,
            )
        ]
    )
    components = compute_components(sr, make_indicator_result(), patterns)
    assert components["market_context"].value == pytest.approx(80.0)


def test_component_pattern_strength_no_match_is_low() -> None:
    sr = make_strategy_result(direction=StrategyDirection.BULLISH)
    components = compute_components(sr, make_indicator_result(), make_pattern_report([]))
    assert components["pattern_strength"].value == pytest.approx(30.0)
