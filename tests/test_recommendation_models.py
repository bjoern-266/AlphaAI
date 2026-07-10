"""Tests für die fünf Recommendation-Modelle (recommendation/*.py)."""

from __future__ import annotations

import pytest

from models.recommendation import RecommendationStrength, SuggestedAction
from models.risk import RiskLevel
from models.strategy import StrategyDirection
from recommendation.base import RecommendationParameterError
from recommendation.confidence_model import ConfidenceModel
from recommendation.decision_model import DecisionModel
from recommendation.explanation_model import ExplanationModel
from recommendation.recommendation_model import RecommendationModel
from recommendation.summary_model import SummaryModel
from tests.helpers import (
    make_recommendation_context,
    make_risk_result,
    make_score_result,
    make_strategy_result,
)

REC_PARAMS = {
    "very_high_min": 80.0,
    "high_min": 65.0,
    "medium_min": 45.0,
    "low_min": 25.0,
    "max_overall_risk_for_high": 66.0,
    "min_consensus_for_high": 60.0,
    "min_data_quality": 60.0,
}
EXPL_PARAMS = {
    "good_market_quality": 60.0,
    "good_volume_quality": 60.0,
    "weak_data_quality": 70.0,
    "elevated_component_risk": 60.0,
}


def _two_confirm_context(**score_kw):
    s1 = make_strategy_result(hypothesis_id="h1")
    s2 = make_strategy_result(hypothesis_id="h2")
    score = make_score_result(hypothesis_id="h1", **score_kw)
    return make_recommendation_context(strategy_result=s1, score_result=score, strategies=[s1, s2])


# --- Decision ----------------------------------------------------------------


def test_decision_model_exposes_rating() -> None:
    ctx = make_recommendation_context()
    out = DecisionModel().compute(ctx, {})
    assert out.value == pytest.approx(ctx.overall_rating)
    assert out.details["factors"]


# --- Recommendation (Stärke + Gates) -----------------------------------------


def test_recommendation_two_confirm_strong() -> None:
    ctx = _two_confirm_context(total_score=95, market_score=80)
    out = RecommendationModel().compute(ctx, REC_PARAMS)
    assert out.details["strength"] in (
        RecommendationStrength.VERY_HIGH,
        RecommendationStrength.HIGH,
    )
    assert out.details["action"] is SuggestedAction.OPEN


def test_recommendation_single_strategy_capped() -> None:
    ctx = make_recommendation_context(
        score_result=make_score_result(total_score=95, market_score=90)
    )
    out = RecommendationModel().compute(ctx, REC_PARAMS)
    # Konsens 50 < 60 -> höchstens MEDIUM (Score allein reicht nicht).
    assert out.details["strength"] is RecommendationStrength.MEDIUM


def test_recommendation_high_risk_capped() -> None:
    risk = make_risk_result(overall_risk=80.0, risk_level=RiskLevel.HIGH)
    s1 = make_strategy_result(hypothesis_id="h1")
    s2 = make_strategy_result(hypothesis_id="h2")
    ctx = make_recommendation_context(
        strategy_result=s1,
        risk_result=risk,
        strategies=[s1, s2],
        score_result=make_score_result(hypothesis_id="h1", total_score=95),
    )
    out = RecommendationModel().compute(ctx, REC_PARAMS)
    assert out.details["strength"] is RecommendationStrength.MEDIUM


def test_recommendation_neutral_capped_to_low() -> None:
    strat = make_strategy_result(direction=StrategyDirection.NEUTRAL)
    ctx = make_recommendation_context(strategy_result=strat, strategies=[strat])
    out = RecommendationModel().compute(ctx, REC_PARAMS)
    assert out.details["strength"] in (RecommendationStrength.LOW, RecommendationStrength.REJECT)


def test_recommendation_low_data_quality_capped() -> None:
    ctx = _two_confirm_context(total_score=95, market_score=80, data_quality=30)
    out = RecommendationModel().compute(ctx, REC_PARAMS)
    assert out.details["strength"] in (RecommendationStrength.LOW, RecommendationStrength.REJECT)


def test_recommendation_missing_param_raises() -> None:
    ctx = make_recommendation_context()
    with pytest.raises(RecommendationParameterError):
        RecommendationModel().compute(ctx, {"very_high_min": 80.0})


# --- Confidence --------------------------------------------------------------


def test_confidence_model_returns_base_confidence() -> None:
    ctx = make_recommendation_context()
    out = ConfidenceModel().compute(ctx, {})
    assert out.value == pytest.approx(ctx.base_confidence)
    assert 0.0 <= out.value <= 1.0


# --- Summary -----------------------------------------------------------------


def test_summary_model_mentions_symbol_and_rating() -> None:
    ctx = make_recommendation_context(symbol="AAPL")
    out = SummaryModel().compute(ctx, {})
    body = out.details["summary"]
    assert "AAPL" in body
    assert "Rating" in body


# --- Explanation -------------------------------------------------------------


def test_explanation_reasons_include_strategy_and_score() -> None:
    strat = make_strategy_result(hypothesis_id="h1")
    ctx = make_recommendation_context(
        strategy_result=strat,
        score_result=make_score_result(hypothesis_id="h1"),
        strategies=[strat],
    )
    out = ExplanationModel().compute(ctx, EXPL_PARAMS)
    reasons = out.details["reasons"]
    assert any("Score" in r for r in reasons)
    assert any("Risk" in r for r in reasons)


def test_explanation_warns_on_weak_data_quality() -> None:
    ctx = make_recommendation_context(score_result=make_score_result(data_quality=40.0))
    out = ExplanationModel().compute(ctx, EXPL_PARAMS)
    assert any("Datenqualität" in w for w in out.details["warnings"])


def test_explanation_warns_on_elevated_component() -> None:
    risk = make_risk_result(risk_components={"gap": 80.0, "data_quality": 0.0})
    ctx = make_recommendation_context(risk_result=risk)
    out = ExplanationModel().compute(ctx, EXPL_PARAMS)
    assert any("gap" in w for w in out.details["warnings"])


def test_explanation_missing_param_raises() -> None:
    ctx = make_recommendation_context()
    with pytest.raises(RecommendationParameterError):
        ExplanationModel().compute(ctx, {})
