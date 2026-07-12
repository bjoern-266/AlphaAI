"""Tests der Market Intelligence Engine und des Regel-Ladens."""

from __future__ import annotations

import copy

import pytest

from engines.market_intelligence_cache import OpportunityCache
from engines.market_intelligence_engine import (
    MarketIntelligenceEngine,
    MarketIntelligenceRulesError,
    load_market_intelligence_rules,
    load_market_intelligence_rules_from_dict,
)
from models.opportunity import MarketCandidate, OpportunityReport
from models.recommendation import Direction, RecommendationStrength
from tests.market_intelligence_helpers import make_candidate, make_full_candidate

_RULES = {
    "meta": {"version": 3},
    "scoring": {"score_min": 0.0, "score_max": 100.0},
    "ranking": {"default_sort": "opportunity_score"},
    "watchlist": {"watchlist_top_size": 10, "watchlist_long_size": 10, "watchlist_short_size": 10},
    "statistics": {"stat_top_sectors": 5, "stat_top_markets": 5},
    "recommendation": {"enabled": True, "weight": 0.40},
    "risk": {"enabled": True, "weight": 0.20},
    "analytics": {"enabled": True, "weight": 0.15},
    "backtest": {"enabled": True, "weight": 0.15},
    "paper_trading": {"enabled": True, "weight": 0.10},
}


def _rules(**overrides):
    data = copy.deepcopy(_RULES)
    for section, values in overrides.items():
        if isinstance(values, dict):
            data.setdefault(section, {}).update(values)
        else:
            data[section] = values
    return load_market_intelligence_rules_from_dict(data)


def _engine(**overrides) -> MarketIntelligenceEngine:
    return MarketIntelligenceEngine(rules=_rules(**overrides))


# --- Regel-Laden ----------------------------------------------------------- #


def test_load_from_default_file():
    rules = load_market_intelligence_rules()
    assert rules.version >= 1
    assert "recommendation" in rules.models


def test_load_from_dict_ok():
    rules = _rules()
    assert rules.version == 3
    assert set(rules.models) == {
        "recommendation",
        "risk",
        "analytics",
        "backtest",
        "paper_trading",
    }


def test_no_models_raises():
    with pytest.raises(MarketIntelligenceRulesError):
        load_market_intelligence_rules_from_dict({"meta": {"version": 1}})


def test_weights_not_summing_to_one_raises():
    with pytest.raises(MarketIntelligenceRulesError):
        _rules(paper_trading={"enabled": True, "weight": 0.5})


def test_disabled_model_excluded_from_weight_sum():
    # recommendation 0.4 + risk 0.2 + analytics 0.15 + backtest 0.15 + paper 0.1 = 1.0;
    # deaktiviere paper und erhoehe risk auf 0.3 -> Summe wieder 1.0.
    rules = _rules(
        risk={"enabled": True, "weight": 0.30},
        paper_trading={"enabled": False, "weight": 0.10},
    )
    assert rules.models["paper_trading"]["enabled"] is False


def test_negative_weight_raises():
    with pytest.raises(MarketIntelligenceRulesError):
        _rules(risk={"enabled": True, "weight": -0.1})


def test_bad_section_type_raises():
    data = copy.deepcopy(_RULES)
    data["ranking"] = "not-a-table"
    with pytest.raises(MarketIntelligenceRulesError):
        load_market_intelligence_rules_from_dict(data)


def test_missing_file_raises(tmp_path):
    with pytest.raises(MarketIntelligenceRulesError):
        load_market_intelligence_rules(tmp_path / "nope.toml")


def test_config_carries_sections():
    rules = _rules()
    assert rules.config["default_sort"] == "opportunity_score"
    assert rules.config["watchlist_top_size"] == 10
    assert rules.config["stat_top_sectors"] == 5


# --- analyze --------------------------------------------------------------- #


def test_analyze_empty_is_invalid():
    report = _engine().analyze([])
    assert report.valid is False
    assert report.opportunity_count == 0
    assert any("Keine Kandidaten" in w for w in report.warnings)


def test_analyze_returns_report():
    report = _engine().analyze([make_full_candidate("AAPL")])
    assert isinstance(report, OpportunityReport)
    assert report.valid is True
    assert report.opportunity_count == 1


def test_analyze_ranks_by_score():
    candidates = [
        make_full_candidate("LOW", rating=40.0, risk_factor=30.0),
        make_full_candidate("HIGH", rating=95.0, risk_factor=90.0),
    ]
    report = _engine().analyze(candidates)
    assert report.opportunities[0].ticker == "HIGH"
    assert report.opportunities[0].opportunity_rank == 1
    assert report.opportunities[1].opportunity_rank == 2


def test_analyze_skips_duplicate_ticker():
    candidates = [make_full_candidate("AAPL"), make_full_candidate("AAPL")]
    report = _engine().analyze(candidates)
    assert report.opportunity_count == 1
    assert any("Doppelter" in w for w in report.warnings)


def test_analyze_skips_empty_ticker():
    report = _engine().analyze([MarketCandidate(ticker="")])
    assert report.opportunity_count == 0
    assert any("ohne Ticker" in w for w in report.warnings)


def test_analyze_watch_candidate_without_recommendation():
    report = _engine().analyze([make_candidate("WCH", with_recommendation=False)])
    assert report.opportunities[0].is_watch
    assert any("keine Empfehlung" in w for w in report.warnings)


def test_analyze_statistics_present():
    candidates = [
        make_full_candidate("A", direction=Direction.LONG),
        make_full_candidate("B", direction=Direction.SHORT),
    ]
    report = _engine().analyze(candidates)
    assert report.statistics.analyzed_count == 2
    assert report.statistics.long_count == 1
    assert report.statistics.short_count == 1


def test_analyze_watchlists_present():
    report = _engine().analyze([make_full_candidate("A", direction=Direction.LONG)])
    assert "top" in report.watchlists
    assert report.watchlists["top"].tickers == ("A",)


def test_analyze_explanations_present():
    report = _engine().analyze([make_full_candidate("A")])
    assert "A" in report.explanations
    assert report.explanations["A"].rank == 1


def test_analyze_metadata():
    report = _engine().analyze([make_full_candidate("A")])
    assert report.metadata["candidate_count"] == 1
    assert report.metadata["opportunity_count"] == 1
    assert report.metadata["rules_version"] == 3


def test_analyze_alternative_sort_from_config():
    engine = _engine(ranking={"default_sort": "alphabetical"})
    report = engine.analyze([make_full_candidate("Z"), make_full_candidate("A")])
    assert [o.ticker for o in report.opportunities] == ["A", "Z"]


def test_disabled_model_not_run():
    # Deaktiviere Analytics/Backtest/Paper, verteile Gewicht auf rec+risk (0.7+0.3).
    engine = _engine(
        recommendation={"enabled": True, "weight": 0.7},
        risk={"enabled": True, "weight": 0.3},
        analytics={"enabled": False, "weight": 0.15},
        backtest={"enabled": False, "weight": 0.15},
        paper_trading={"enabled": False, "weight": 0.10},
    )
    report = engine.analyze([make_full_candidate("A", rating=80.0, risk_factor=60.0)])
    # 80*0.7 + 60*0.3 = 74
    assert report.opportunities[0].opportunity_score == pytest.approx(74.0)


def test_unregistered_model_warns():
    from engines.market_intelligence_registry import MarketIntelligenceRegistry
    from market_intelligence.opportunity import RecommendationOpportunityModel

    registry = MarketIntelligenceRegistry()
    registry.register(RecommendationOpportunityModel())  # nur ein Modell registriert
    engine = MarketIntelligenceEngine(rules=_rules(), registry=registry)
    report = engine.analyze([make_full_candidate("A")])
    assert any("nicht registriert" in w for w in report.warnings)


def test_from_config_builds_engine():
    engine = MarketIntelligenceEngine.from_config()
    report = engine.analyze([make_full_candidate("A")])
    assert report.opportunity_count == 1


def test_cache_returns_same_report():
    cache = OpportunityCache()
    engine = MarketIntelligenceEngine(rules=_rules(), cache=cache)
    candidates = [make_full_candidate("A")]
    first = engine.analyze(candidates)
    second = engine.analyze(candidates)
    assert first is second
    assert cache.hits == 1


def test_calculation_time_recorded():
    clock = iter([1.0, 1.5])
    engine = MarketIntelligenceEngine(rules=_rules(), timer=lambda: next(clock))
    report = engine.analyze([make_full_candidate("A")])
    assert report.calculation_time == pytest.approx(0.5)


def test_scores_within_bounds():
    report = _engine().analyze([make_full_candidate("A", rating=200.0, risk_factor=200.0)])
    assert 0.0 <= report.opportunities[0].opportunity_score <= 100.0


def test_strength_preserved_in_opportunity():
    report = _engine().analyze(
        [make_full_candidate("A", strength=RecommendationStrength.VERY_HIGH)]
    )
    assert report.opportunities[0].recommendation_strength is RecommendationStrength.VERY_HIGH
