"""Tests der Bewertungsmodelle und des Opportunity-Aufbaus."""

from __future__ import annotations

import pytest

from core.exceptions import MarketIntelligenceParameterError
from market_intelligence.base import clamp_score, require_weight
from market_intelligence.opportunity import (
    AnalyticsOpportunityModel,
    BacktestOpportunityModel,
    PaperTradingOpportunityModel,
    RecommendationOpportunityModel,
    RiskOpportunityModel,
    build_opportunity,
)
from models.opportunity import MarketCandidate, MarketIntelligenceContext
from models.recommendation import Direction, RecommendationStrength
from tests.market_intelligence_helpers import make_candidate, make_full_candidate

_CONFIG = {"score_min": 0.0, "score_max": 100.0}


def _ctx(candidate: MarketCandidate) -> MarketIntelligenceContext:
    return MarketIntelligenceContext(candidate=candidate, config=_CONFIG)


# --- Hilfsfunktionen ------------------------------------------------------- #


def test_require_weight_ok():
    assert require_weight({"weight": 0.4}, "m") == 0.4


def test_require_weight_missing():
    with pytest.raises(MarketIntelligenceParameterError):
        require_weight({}, "m")


def test_require_weight_out_of_range():
    with pytest.raises(MarketIntelligenceParameterError):
        require_weight({"weight": 1.5}, "m")


def test_require_weight_rejects_bool():
    with pytest.raises(MarketIntelligenceParameterError):
        require_weight({"weight": True}, "m")


def test_clamp_score_bounds():
    assert clamp_score(150.0, _CONFIG) == 100.0
    assert clamp_score(-5.0, _CONFIG) == 0.0
    assert clamp_score(42.0, _CONFIG) == 42.0


# --- Recommendation-Modell ------------------------------------------------- #


def test_recommendation_model_uses_rating():
    out = RecommendationOpportunityModel().compute(
        _ctx(make_candidate(rating=82.0)), {"weight": 0.4}
    )
    assert out.available is True
    assert out.score == 82.0
    assert out.weight == 0.4
    assert any("Rating" in r for r in out.reasons)


def test_recommendation_model_unavailable_without_recommendation():
    out = RecommendationOpportunityModel().compute(
        _ctx(make_candidate(with_recommendation=False)), {"weight": 0.4}
    )
    assert out.available is False
    assert out.score == 0.0


def test_recommendation_model_clamps():
    out = RecommendationOpportunityModel().compute(
        _ctx(make_candidate(rating=150.0)), {"weight": 0.4}
    )
    assert out.score == 100.0


# --- Risk-Modell ----------------------------------------------------------- #


def test_risk_model_uses_factor():
    out = RiskOpportunityModel().compute(_ctx(make_candidate(risk_factor=65.0)), {"weight": 0.2})
    assert out.available is True
    assert out.score == 65.0


def test_risk_model_unavailable_without_recommendation():
    out = RiskOpportunityModel().compute(
        _ctx(make_candidate(with_recommendation=False)), {"weight": 0.2}
    )
    assert out.available is False


# --- Win-Rate-Modelle ------------------------------------------------------ #


def test_analytics_model_win_rate():
    out = AnalyticsOpportunityModel().compute(
        _ctx(make_candidate(with_analytics=True)), {"weight": 0.15}
    )
    assert out.available is True
    assert out.score == pytest.approx(55.0)  # win_rate 0.55 * 100


def test_analytics_model_unavailable():
    out = AnalyticsOpportunityModel().compute(_ctx(make_candidate()), {"weight": 0.15})
    assert out.available is False


def test_backtest_model_win_rate():
    out = BacktestOpportunityModel().compute(
        _ctx(make_candidate(with_backtest=True)), {"weight": 0.15}
    )
    assert out.available is True
    assert out.score == pytest.approx(66.0)  # win_rate 0.66 * 100


def test_backtest_model_unavailable():
    out = BacktestOpportunityModel().compute(_ctx(make_candidate()), {"weight": 0.15})
    assert out.available is False


def test_paper_model_win_rate():
    out = PaperTradingOpportunityModel().compute(
        _ctx(make_candidate(with_paper=True)), {"weight": 0.1}
    )
    assert out.available is True
    assert out.score == pytest.approx(60.0)  # win_rate 0.60 * 100


def test_paper_model_unavailable():
    out = PaperTradingOpportunityModel().compute(_ctx(make_candidate()), {"weight": 0.1})
    assert out.available is False


def test_all_models_require_weight():
    models = [
        RecommendationOpportunityModel(),
        RiskOpportunityModel(),
        AnalyticsOpportunityModel(),
        BacktestOpportunityModel(),
        PaperTradingOpportunityModel(),
    ]
    for model in models:
        with pytest.raises(MarketIntelligenceParameterError):
            model.compute(_ctx(make_full_candidate()), {})


# --- build_opportunity ----------------------------------------------------- #


def _run_all(candidate: MarketCandidate) -> dict:
    ctx = _ctx(candidate)
    weights = {
        "recommendation": 0.40,
        "risk": 0.20,
        "analytics": 0.15,
        "backtest": 0.15,
        "paper_trading": 0.10,
    }
    models = {
        "recommendation": RecommendationOpportunityModel(),
        "risk": RiskOpportunityModel(),
        "analytics": AnalyticsOpportunityModel(),
        "backtest": BacktestOpportunityModel(),
        "paper_trading": PaperTradingOpportunityModel(),
    }
    return {name: models[name].compute(ctx, {"weight": weights[name]}) for name in models}


def test_build_opportunity_weighted_score_all_available():
    candidate = make_full_candidate(rating=80.0, risk_factor=60.0)
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    # 80*.4 + 60*.2 + 55*.15 + 66*.15 + 60*.10 = 32+12+8.25+9.9+6 = 68.15
    assert opportunity.opportunity_score == pytest.approx(68.15)


def test_build_opportunity_renormalizes_missing_sources():
    candidate = make_candidate(rating=80.0, risk_factor=60.0)  # nur rec + risk
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    # (80*.4 + 60*.2) / (.4+.2) = 44/.6 = 73.33
    assert opportunity.opportunity_score == pytest.approx(73.3333, abs=1e-3)


def test_build_opportunity_watch_when_no_recommendation():
    candidate = make_candidate(with_recommendation=False)
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    assert opportunity.is_watch
    assert opportunity.opportunity_score == 0.0
    assert opportunity.direction is Direction.NEUTRAL
    assert opportunity.recommendation_strength is RecommendationStrength.REJECT


def test_build_opportunity_copies_recommendation_fields():
    candidate = make_candidate(
        direction=Direction.SHORT, strength=RecommendationStrength.VERY_HIGH, rating=70.0
    )
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    assert opportunity.direction is Direction.SHORT
    assert opportunity.recommendation_strength is RecommendationStrength.VERY_HIGH
    assert opportunity.overall_rating == 70.0
    assert opportunity.risk == 60.0


def test_build_opportunity_records_components():
    candidate = make_full_candidate()
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    assert set(opportunity.components) == {
        "recommendation",
        "risk",
        "analytics",
        "backtest",
        "paper_trading",
    }


def test_build_opportunity_aggregates_reasons_and_warnings():
    candidate = make_full_candidate()
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    assert any("[recommendation]" in r for r in opportunity.reasons)
    assert opportunity.warnings  # aus der Empfehlung übernommen


def test_build_opportunity_summaries_from_sources():
    candidate = make_full_candidate(pattern_summary="FVG", strategy_summary="Trend")
    outputs = _run_all(candidate)
    opportunity = build_opportunity(_ctx(candidate), outputs)
    assert opportunity.pattern_summary == "FVG"
    assert opportunity.strategy_summary == "Trend"
    assert opportunity.analytics_summary  # aus AnalyticsReport
    assert opportunity.backtest_summary  # aus BacktestReport
    assert opportunity.paper_trading_summary  # aus PaperTradingReport


def test_build_opportunity_rank_is_zero_before_ranking():
    candidate = make_full_candidate()
    opportunity = build_opportunity(_ctx(candidate), _run_all(candidate))
    assert opportunity.opportunity_rank == 0
