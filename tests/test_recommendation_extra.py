"""Ergänzende Tests: Report-Hilfen, Faktoren, Handlungen, weitere Logikfälle."""

from __future__ import annotations

import pytest

from engines.recommendation_engine import RecommendationEngine, load_recommendation_rules
from engines.strategy_result import StrategyReport
from models.recommendation import (
    RecommendationLevel,
    RecommendationReport,
    RecommendationResult,
    SuggestedAction,
)
from models.risk import RiskLevel
from models.score import ScoreReport
from recommendation.base import (
    clamp_rating,
    compute_overall_rating,
    level_from_rating,
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

THRESHOLDS = {"strong_buy_min": 80.0, "buy_min": 65.0, "watch_min": 45.0, "wait_min": 25.0}


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


def test_report_by_level() -> None:
    report = _report(n=2, total=95, market=80)
    level = report.results[0].recommendation_level
    assert report.by_level(level)


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
        (80.0, RecommendationLevel.STRONG_BUY),
        (79.9, RecommendationLevel.BUY),
        (65.0, RecommendationLevel.BUY),
        (64.9, RecommendationLevel.WATCH),
        (45.0, RecommendationLevel.WATCH),
        (44.9, RecommendationLevel.WAIT),
        (25.0, RecommendationLevel.WAIT),
        (24.9, RecommendationLevel.AVOID),
    ],
)
def test_level_thresholds_boundaries(rating: float, expected: RecommendationLevel) -> None:
    assert level_from_rating(rating, THRESHOLDS) is expected


# --- Handlungs-Zuordnung im Ergebnis -----------------------------------------


def test_action_open_for_buy_levels() -> None:
    r = _report(n=2, total=95, market=80).results[0]
    if r.recommendation_level in (RecommendationLevel.STRONG_BUY, RecommendationLevel.BUY):
        assert r.suggested_action is SuggestedAction.OPEN


def test_action_monitor_for_watch() -> None:
    # Einzelne Strategie -> WATCH -> MONITOR.
    r = _report(n=1, total=95, market=90).results[0]
    assert r.recommendation_level is RecommendationLevel.WATCH
    assert r.suggested_action is SuggestedAction.MONITOR


def test_avoid_maps_to_skip() -> None:
    r = _report(n=1, total=5, market=5, risk_overall=95, risk_level=RiskLevel.HIGH, dq=10).results[
        0
    ]
    if r.recommendation_level is RecommendationLevel.AVOID:
        assert r.suggested_action is SuggestedAction.SKIP


# --- No-Trade-Philosophie ist vollwertig -------------------------------------


def test_wait_is_a_valid_recommendation() -> None:
    r = _report(n=1, total=40, market=30).results[0]
    assert isinstance(r, RecommendationResult)
    assert r.recommendation_level in (
        RecommendationLevel.WATCH,
        RecommendationLevel.WAIT,
        RecommendationLevel.AVOID,
    )
    # Auch ohne Trade ist die Empfehlung vollständig erklärbar.
    assert r.reasons
    assert r.summary


def test_multiple_confirmations_raise_relative_to_single() -> None:
    single = _report(n=1, total=90, market=80).results[0]
    multi = _report(n=2, total=90, market=80).results[0]
    assert multi.overall_rating >= single.overall_rating
