"""Ergänzende Tests: Report-Hilfen, Faktoren, Handlungen, weitere Logikfälle."""

from __future__ import annotations

import pytest

from engines.recommendation_engine import RecommendationEngine, load_recommendation_rules
from engines.strategy_result import StrategyReport
from models.recommendation import (
    RecommendationReport,
    RecommendationResult,
    RecommendationStrength,
    SuggestedAction,
)
from models.risk import RiskLevel
from models.score import ScoreReport
from recommendation.base import (
    clamp_rating,
    compute_overall_rating,
    strength_from_rating,
    weighted_sum,
)
from tests.helpers import (
    _REC_FACTOR_WEIGHTS,
    make_recommendation_context,
    make_risk_report,
    make_risk_result,
    make_score_result,
    make_strategy_result,
)

THRESHOLDS = {"very_high_min": 80.0, "high_min": 65.0, "medium_min": 45.0, "low_min": 25.0}


def _engine() -> RecommendationEngine:
    return RecommendationEngine(rules=load_recommendation_rules())


def _reports(n=2, total=91.0, market=70.0, risk_overall=20.0, risk_level=RiskLevel.LOW, dq=100.0):
    strategies, scores, risks = [], [], []
    for i in range(1, n + 1):
        hyp = f"h{i}"
        strategies.append(make_strategy_result(hypothesis_id=hyp, strength=70.0, confidence=0.7))
        scores.append(
            make_score_result(
                score_id=f"score:{hyp}",
                hypothesis_id=hyp,
                total_score=total,
                market_score=market,
                data_quality=dq,
            )
        )
        risks.append(
            make_risk_result(hypothesis_id=hyp, overall_risk=risk_overall, risk_level=risk_level)
        )
    return (
        StrategyReport(results=strategies, valid=True),
        ScoreReport(results=scores, valid=True),
        make_risk_report(results=risks, valid=True),
    )


# --- Report-Hilfen -----------------------------------------------------------


def _report(**kw) -> RecommendationReport:
    return _engine().recommend(*_reports(**kw))


def test_report_by_strength() -> None:
    report = _report(n=2, total=95, market=80)
    strength = report.results[0].recommendation_strength
    assert report.by_strength(strength)


def test_report_by_direction() -> None:
    report = _report(n=2, total=95, market=80)
    direction = report.results[0].direction
    assert report.by_direction(direction)


def test_report_by_action() -> None:
    report = _report(n=2, total=95, market=80)
    assert report.by_action(SuggestedAction.OPEN)


def test_report_top_sorts_by_rating() -> None:
    report = _report(n=2)
    top = report.top(2)
    assert top[0].overall_rating >= top[-1].overall_rating


def test_report_recommendation_count() -> None:
    assert _report(n=3).recommendation_count == 3


def test_calculation_time_is_set() -> None:
    report = _report(n=1)
    assert report.calculation_time >= 0.0


def test_timestamp_propagated_from_score() -> None:
    report = _report(n=1)
    assert report.results[0].timestamp is not None


# --- Faktoren / Rating -------------------------------------------------------


def test_weighted_sum_helper() -> None:
    assert weighted_sum({"a": 0.5, "b": 0.5}, {"a": 100.0, "b": 0.0}) == pytest.approx(50.0)


def test_market_quality_factor_from_market_score() -> None:
    ctx = make_recommendation_context(score_result=make_score_result(market_score=42.0))
    assert ctx.factors["market_quality"].value == pytest.approx(42.0)


def test_strategy_factor_from_strength() -> None:
    strat = make_strategy_result(strength=64.0)
    ctx = make_recommendation_context(strategy_result=strat, strategies=[strat])
    assert ctx.factors["strategy"].value == pytest.approx(64.0)


def test_data_quality_factor() -> None:
    ctx = make_recommendation_context(score_result=make_score_result(data_quality=55.0))
    assert ctx.factors["data_quality"].value == pytest.approx(55.0)


def test_overall_rating_matches_manual() -> None:
    ctx = make_recommendation_context()
    values = {n: f.value for n, f in ctx.factors.items()}
    assert compute_overall_rating(ctx.factors, _REC_FACTOR_WEIGHTS) == pytest.approx(
        clamp_rating(weighted_sum(_REC_FACTOR_WEIGHTS, values))
    )


# --- Stufen an Schwellen -----------------------------------------------------


@pytest.mark.parametrize(
    "rating,expected",
    [
        (80.0, RecommendationStrength.VERY_HIGH),
        (79.9, RecommendationStrength.HIGH),
        (65.0, RecommendationStrength.HIGH),
        (64.9, RecommendationStrength.MEDIUM),
        (45.0, RecommendationStrength.MEDIUM),
        (44.9, RecommendationStrength.LOW),
        (25.0, RecommendationStrength.LOW),
        (24.9, RecommendationStrength.REJECT),
    ],
)
def test_strength_thresholds_boundaries(rating: float, expected: RecommendationStrength) -> None:
    assert strength_from_rating(rating, THRESHOLDS) is expected


# --- Handlungs-Zuordnung im Ergebnis -----------------------------------------


def test_action_open_for_high_strengths() -> None:
    r = _report(n=2, total=95, market=80).results[0]
    if r.recommendation_strength in (
        RecommendationStrength.VERY_HIGH,
        RecommendationStrength.HIGH,
    ):
        assert r.suggested_action is SuggestedAction.OPEN


def test_action_monitor_for_medium() -> None:
    # Einzelne Strategie -> MEDIUM -> MONITOR.
    r = _report(n=1, total=95, market=90).results[0]
    assert r.recommendation_strength is RecommendationStrength.MEDIUM
    assert r.suggested_action is SuggestedAction.MONITOR


def test_reject_maps_to_skip() -> None:
    r = _report(n=1, total=5, market=5, risk_overall=95, risk_level=RiskLevel.HIGH, dq=10).results[
        0
    ]
    if r.recommendation_strength is RecommendationStrength.REJECT:
        assert r.suggested_action is SuggestedAction.SKIP


# --- No-Trade-Philosophie ist vollwertig -------------------------------------


def test_low_strength_is_a_valid_recommendation() -> None:
    r = _report(n=1, total=40, market=30).results[0]
    assert isinstance(r, RecommendationResult)
    assert r.recommendation_strength in (
        RecommendationStrength.MEDIUM,
        RecommendationStrength.LOW,
        RecommendationStrength.REJECT,
    )
    # Auch ohne Trade ist die Empfehlung vollständig erklärbar.
    assert r.reasons
    assert r.summary


def test_multiple_confirmations_raise_relative_to_single() -> None:
    single = _report(n=1, total=90, market=80).results[0]
    multi = _report(n=2, total=90, market=80).results[0]
    assert multi.overall_rating >= single.overall_rating
