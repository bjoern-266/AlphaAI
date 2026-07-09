"""Tests für die gemeinsamen Recommendation-Hilfsmittel (recommendation/base.py)."""

from __future__ import annotations

import pytest

from models.risk import RiskLevel
from models.strategy import StrategyDirection
from recommendation.base import (
    RECOMMENDATION_FACTOR_NAMES,
    RecommendationLevel,
    RecommendationParameterError,
    SuggestedAction,
    action_for_level,
    cap_level,
    clamp_confidence,
    clamp_rating,
    compute_confidence,
    compute_factors,
    compute_overall_rating,
    consensus_fraction,
    is_neutral,
    level_from_rating,
    level_severity,
    require_float,
    validate_weights,
)
from tests.helpers import (
    _REC_CONFIDENCE_WEIGHTS,
    _REC_FACTOR_WEIGHTS,
    make_risk_result,
    make_score_result,
    make_strategy_result,
)

THRESHOLDS = {"strong_buy_min": 80.0, "buy_min": 65.0, "watch_min": 45.0, "wait_min": 25.0}


def _factors(**kw):
    strat = kw.get("strategy") or make_strategy_result()
    score = kw.get("score") or make_score_result(hypothesis_id=strat.hypothesis_id)
    risk = kw.get("risk") or make_risk_result(hypothesis_id=strat.hypothesis_id)
    strategies = kw.get("strategies", [strat])
    return compute_factors(strat, score, risk, strategies, consensus_full_at=kw.get("full_at", 2))


# --- Faktoren ----------------------------------------------------------------


def test_compute_factors_has_all_names() -> None:
    assert set(_factors()) == set(RECOMMENDATION_FACTOR_NAMES)


def test_factor_score_equals_total_score() -> None:
    score = make_score_result(total_score=88.0)
    assert _factors(score=score)["score"].value == pytest.approx(88.0)


def test_factor_risk_is_inverse_of_overall_risk() -> None:
    risk = make_risk_result(overall_risk=30.0)
    assert _factors(risk=risk)["risk"].value == pytest.approx(70.0)


def test_consensus_single_strategy_is_partial() -> None:
    assert _factors()["consensus"].value == pytest.approx(50.0)


def test_consensus_two_confirming_is_full() -> None:
    s1 = make_strategy_result(hypothesis_id="h1")
    s2 = make_strategy_result(hypothesis_id="h2")
    assert _factors(strategy=s1, strategies=[s1, s2])["consensus"].value == pytest.approx(100.0)


def test_consensus_conflict_reduces() -> None:
    s1 = make_strategy_result(hypothesis_id="h1", direction=StrategyDirection.BULLISH)
    s2 = make_strategy_result(hypothesis_id="h2", direction=StrategyDirection.BEARISH)
    value = _factors(strategy=s1, strategies=[s1, s2])["consensus"].value
    assert value == pytest.approx(25.0)


# --- Rating / Confidence -----------------------------------------------------


def test_overall_rating_in_range() -> None:
    rating = compute_overall_rating(_factors(), _REC_FACTOR_WEIGHTS)
    assert 0.0 <= rating <= 100.0


def test_score_alone_cannot_dominate_rating() -> None:
    # Perfekter Score, aber alles andere schwach -> Rating bleibt niedrig.
    strat = make_strategy_result(strength=0.0, confidence=0.0)
    score = make_score_result(
        hypothesis_id=strat.hypothesis_id, total_score=100.0, market_score=0.0, data_quality=0.0
    )
    risk = make_risk_result(hypothesis_id=strat.hypothesis_id, overall_risk=100.0)
    factors = compute_factors(strat, score, risk, [strat], consensus_full_at=2)
    rating = compute_overall_rating(factors, _REC_FACTOR_WEIGHTS)
    # nur der Score-Anteil (0.25 * 100) + halber Konsens (0.20 * 50) = 35
    assert rating < 45.0


def test_confidence_in_range() -> None:
    conf = compute_confidence(make_strategy_result(), _factors(), _REC_CONFIDENCE_WEIGHTS)
    assert 0.0 <= conf <= 1.0


def test_consensus_fraction_helper() -> None:
    s1 = make_strategy_result(hypothesis_id="h1")
    s2 = make_strategy_result(hypothesis_id="h2")
    assert consensus_fraction(s1, [s1, s2]) == pytest.approx(1.0)
    assert consensus_fraction(s1, []) == 0.0


# --- Stufen / Handlungen -----------------------------------------------------


def test_level_from_rating() -> None:
    assert level_from_rating(85, THRESHOLDS) is RecommendationLevel.STRONG_BUY
    assert level_from_rating(70, THRESHOLDS) is RecommendationLevel.BUY
    assert level_from_rating(50, THRESHOLDS) is RecommendationLevel.WATCH
    assert level_from_rating(30, THRESHOLDS) is RecommendationLevel.WAIT
    assert level_from_rating(10, THRESHOLDS) is RecommendationLevel.AVOID


def test_cap_level() -> None:
    assert cap_level(RecommendationLevel.STRONG_BUY, RecommendationLevel.WATCH) is (
        RecommendationLevel.WATCH
    )
    assert (
        cap_level(RecommendationLevel.WAIT, RecommendationLevel.WATCH) is RecommendationLevel.WAIT
    )


def test_level_severity_order() -> None:
    assert level_severity(RecommendationLevel.AVOID) < level_severity(
        RecommendationLevel.STRONG_BUY
    )


def test_action_for_level() -> None:
    assert action_for_level(RecommendationLevel.STRONG_BUY) is SuggestedAction.OPEN
    assert action_for_level(RecommendationLevel.BUY) is SuggestedAction.OPEN
    assert action_for_level(RecommendationLevel.WATCH) is SuggestedAction.MONITOR
    assert action_for_level(RecommendationLevel.WAIT) is SuggestedAction.WAIT
    assert action_for_level(RecommendationLevel.AVOID) is SuggestedAction.SKIP


def test_is_neutral() -> None:
    assert is_neutral(StrategyDirection.NEUTRAL)
    assert not is_neutral(StrategyDirection.BULLISH)


# --- Parameter / Gewichte ----------------------------------------------------


def test_require_float_errors() -> None:
    assert require_float({"x": 2}, "x", "m") == 2.0
    with pytest.raises(RecommendationParameterError):
        require_float({}, "x", "m")
    with pytest.raises(RecommendationParameterError):
        require_float({"x": -1}, "x", "m")


def test_validate_weights_ok_and_errors() -> None:
    assert validate_weights({"a": 0.5, "b": 0.5}, ("a", "b"), "m") == {"a": 0.5, "b": 0.5}
    with pytest.raises(RecommendationParameterError, match="100"):
        validate_weights({"a": 0.5, "b": 0.4}, ("a", "b"), "m")
    with pytest.raises(RecommendationParameterError, match="fehlende"):
        validate_weights({"a": 1.0}, ("a", "b"), "m")
    with pytest.raises(RecommendationParameterError, match="unbekannte"):
        validate_weights({"a": 0.5, "b": 0.5, "c": 0.0}, ("a", "b"), "m")


def test_clamps() -> None:
    assert clamp_rating(150) == 100.0
    assert clamp_rating(-5) == 0.0
    assert clamp_confidence(2.0) == 1.0
    assert clamp_confidence(-1.0) == 0.0


def test_risk_level_used_in_factor_reason() -> None:
    risk = make_risk_result(overall_risk=20.0, risk_level=RiskLevel.LOW)
    assert "low" in _factors(risk=risk)["risk"].reason
