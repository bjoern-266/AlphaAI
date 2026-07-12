"""Tests des Explainers (transparente Herleitung, keine Blackbox)."""

from __future__ import annotations

from market_intelligence import ranking_engine
from market_intelligence.explainer import build_explanations, explain
from tests.market_intelligence_helpers import make_opportunity


def test_explain_headline_contains_rank_and_ticker():
    opp = make_opportunity("AAPL", score=80.0, rank=1)
    exp = explain(opp)
    assert "Platz 1" in exp.headline
    assert "AAPL" in exp.headline


def test_explain_rank_one_highest():
    opp = make_opportunity("AAPL", rank=1)
    exp = explain(opp, above=None)
    assert "Höchste" in exp.why_not_higher


def test_explain_why_not_higher_compares_above():
    above = make_opportunity("TOP", score=90.0, rank=1)
    opp = make_opportunity("AAPL", score=70.0, rank=2)
    exp = explain(opp, above=above)
    assert "TOP" in exp.why_not_higher
    assert "20" in exp.why_not_higher  # 90 - 70


def test_explain_factors_sorted_by_component_score():
    opp = make_opportunity(
        "AAPL", components={"recommendation": 90.0, "risk": 40.0, "analytics": 60.0}
    )
    exp = explain(opp)
    assert exp.factors[0].startswith("Empfehlung")  # höchste Komponente


def test_explain_factors_limited_to_three():
    opp = make_opportunity(
        "AAPL",
        components={
            "recommendation": 90.0,
            "risk": 80.0,
            "analytics": 70.0,
            "backtest": 60.0,
            "paper_trading": 50.0,
        },
    )
    exp = explain(opp)
    assert len(exp.factors) == 3


def test_explain_risks_include_warnings():
    opp = make_opportunity("AAPL", warnings=("Spread erhöht",))
    exp = explain(opp)
    assert any("Spread" in r for r in exp.risks)


def test_explain_risks_include_risk_factor():
    opp = make_opportunity("AAPL", risk=55.0)
    exp = explain(opp)
    assert any("Risiko-Faktor" in r for r in exp.risks)


def test_explain_no_risk_factor_when_none():
    opp = make_opportunity("AAPL", risk=None, warnings=())
    exp = explain(opp)
    assert exp.risks == ()


def test_build_explanations_keyed_by_ticker():
    opps = [
        make_opportunity("A", score=90.0),
        make_opportunity("B", score=70.0),
        make_opportunity("C", score=50.0),
    ]
    ranked = ranking_engine.rank(opps)
    explanations = build_explanations(ranked)
    assert set(explanations) == {"A", "B", "C"}


def test_build_explanations_first_has_no_above():
    ranked = ranking_engine.rank([make_opportunity("A", score=90.0), make_opportunity("B", 70.0)])
    explanations = build_explanations(ranked)
    assert "Höchste" in explanations["A"].why_not_higher
    assert "A" in explanations["B"].why_not_higher


def test_build_explanations_carries_rank():
    ranked = ranking_engine.rank([make_opportunity("A", 90.0), make_opportunity("B", 70.0)])
    explanations = build_explanations(ranked)
    assert explanations["A"].rank == 1
    assert explanations["B"].rank == 2


def test_build_explanations_empty():
    assert build_explanations([]) == {}


def test_explain_score_recorded():
    exp = explain(make_opportunity("A", score=42.0, rank=3))
    assert exp.opportunity_score == 42.0
    assert exp.rank == 3
