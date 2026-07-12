"""Tests der Market Discovery Engine und des Regel-Ladens."""

from __future__ import annotations

import copy

import pytest

from engines.market_discovery_cache import DiscoveryCache
from engines.market_discovery_engine import (
    MarketDiscoveryEngine,
    MarketDiscoveryRulesError,
    load_market_discovery_rules,
    load_market_discovery_rules_from_dict,
)
from engines.market_intelligence_engine import MarketIntelligenceEngine
from models.market_discovery import DiscoveryReport
from models.recommendation import Direction, RecommendationStrength
from tests.market_discovery_helpers import (
    make_analysis,
    make_analysis_provider,
    make_symbol,
    make_symbol_source,
)

_RULES = {
    "meta": {"version": 2},
    "universe": {"default_markets": ["sp500", "dax"]},
    "filter": {
        "min_price": 1.0,
        "min_volume": 100_000.0,
        "min_dollar_volume": 1_000_000.0,
        "min_history_days": 200,
        "require_tradable": True,
        "exclude_delisted": True,
        "exclude_penny": True,
        "penny_price": 1.0,
    },
    "balancing": {"enabled": True, "max_streak": 2},
    "statistics": {"top_sectors": 5, "top_markets": 5},
    "discovery": {"top_opportunities": 10},
}


def _rules(**overrides):
    data = copy.deepcopy(_RULES)
    for section, values in overrides.items():
        if isinstance(values, dict):
            data.setdefault(section, {}).update(values)
        else:
            data[section] = values
    return load_market_discovery_rules_from_dict(data)


def _engine(**overrides) -> MarketDiscoveryEngine:
    return MarketDiscoveryEngine(
        rules=_rules(**overrides), intelligence=MarketIntelligenceEngine.from_config()
    )


def _universe():
    return {
        "sp500": [
            make_symbol("AAPL", sector="Tech", market="sp500"),
            make_symbol("NVDA", sector="Semi", market="sp500"),
            make_symbol("PENNY", sector="Junk", market="sp500", price=0.4),
            make_symbol("DEAD", sector="Tech", market="sp500", delisted=True),
        ],
        "dax": [make_symbol("SAP", sector="Software", country="DE", market="dax")],
    }


def _analyses():
    return {
        "AAPL": make_analysis("AAPL", Direction.LONG, RecommendationStrength.VERY_HIGH, 90.0, 80.0),
        "NVDA": make_analysis("NVDA", Direction.LONG, RecommendationStrength.HIGH, 85.0, 70.0),
        "SAP": make_analysis("SAP", Direction.SHORT, RecommendationStrength.MEDIUM, 55.0, 45.0),
    }


def _discover(engine=None, markets=None):
    engine = engine or _engine()
    return engine.discover(
        markets=markets if markets is not None else ["sp500", "dax"],
        symbol_source=make_symbol_source(_universe()),
        analysis_provider=make_analysis_provider(_analyses()),
    )


# --- Regel-Laden ----------------------------------------------------------- #


def test_load_from_default_file():
    rules = load_market_discovery_rules()
    assert rules.version >= 1
    assert "default_markets" in rules.universe


def test_load_from_dict():
    rules = _rules()
    assert rules.version == 2
    assert rules.universe["default_markets"] == ["sp500", "dax"]
    assert rules.filter["min_price"] == 1.0


def test_bad_section_type_raises():
    data = copy.deepcopy(_RULES)
    data["filter"] = "not-a-table"
    with pytest.raises(MarketDiscoveryRulesError):
        load_market_discovery_rules_from_dict(data)


def test_bad_default_markets_type_raises():
    with pytest.raises(MarketDiscoveryRulesError):
        _rules(universe={"default_markets": "sp500"})


def test_missing_file_raises(tmp_path):
    with pytest.raises(MarketDiscoveryRulesError):
        load_market_discovery_rules(tmp_path / "nope.toml")


# --- discover -------------------------------------------------------------- #


def test_discover_returns_report():
    report = _discover()
    assert isinstance(report, DiscoveryReport)
    assert report.valid is True


def test_discover_filters_candidates():
    report = _discover()
    # PENNY + DEAD werden verworfen; AAPL/NVDA/SAP bleiben.
    assert report.statistics.universe_count == 5
    assert report.statistics.rejected_count == 2
    assert report.statistics.analyzed_count == 3


def test_discover_rejection_reasons():
    report = _discover()
    reasons = {r.ticker: r.reason for r in report.rejected}
    assert reasons["PENNY"] == "Penny Stock"
    assert reasons["DEAD"] == "delisted"


def test_discover_ranks_opportunities():
    report = _discover()
    assert report.opportunities[0].rank == 1
    scores = [o.opportunity_score for o in report.opportunities]
    assert scores == sorted(scores, reverse=True)


def test_discover_best_is_aapl():
    report = _discover()
    assert report.opportunities[0].ticker == "AAPL"


def test_discover_country_flows_through():
    report = _discover()
    assert report.by_ticker("SAP").country == "DE"
    assert report.by_ticker("AAPL").country == "US"


def test_discover_uses_default_markets_when_none():
    report = _engine().discover(
        symbol_source=make_symbol_source(_universe()),
        analysis_provider=make_analysis_provider(_analyses()),
    )
    assert set(report.markets) == {"sp500", "dax"}


def test_discover_unknown_market_warns():
    report = _discover(markets=["sp500", "bogus"])
    assert any("bogus" in w for w in report.warnings)


def test_discover_empty_universe_invalid():
    report = _engine().discover(markets=["sp500"])  # leere Symbol-Quelle
    assert report.valid is False
    assert report.opportunity_count == 0
    assert any("Leeres Universum" in w for w in report.warnings)


def test_discover_statistics_counts_directions():
    report = _discover()
    assert report.statistics.long_count == 2
    assert report.statistics.short_count == 1


def test_discover_top_markets():
    report = _discover()
    markets = dict(report.statistics.top_markets)
    assert markets["sp500"] == 2
    assert markets["dax"] == 1


def test_discover_metadata_version():
    report = _discover()
    assert report.metadata["rules_version"] == 2


def test_from_config_builds_engine():
    engine = MarketDiscoveryEngine.from_config()
    report = engine.discover(
        markets=["sp500"],
        symbol_source=make_symbol_source(_universe()),
        analysis_provider=make_analysis_provider(_analyses()),
    )
    assert report.opportunity_count == 2  # AAPL + NVDA (PENNY/DEAD raus)


def test_cache_returns_same_report():
    cache = DiscoveryCache()
    engine = MarketDiscoveryEngine(
        rules=_rules(), intelligence=MarketIntelligenceEngine.from_config(), cache=cache
    )
    source = make_symbol_source(_universe())
    provider = make_analysis_provider(_analyses())
    first = engine.discover(markets=["sp500"], symbol_source=source, analysis_provider=provider)
    second = engine.discover(markets=["sp500"], symbol_source=source, analysis_provider=provider)
    assert first is second
    assert cache.hits == 1


def test_calculation_time_recorded():
    clock = iter([1.0, 1.25])
    engine = MarketDiscoveryEngine(
        rules=_rules(),
        intelligence=MarketIntelligenceEngine.from_config(),
        timer=lambda: next(clock),
    )
    report = engine.discover(
        markets=["sp500"],
        symbol_source=make_symbol_source(_universe()),
        analysis_provider=make_analysis_provider(_analyses()),
    )
    assert report.calculation_time == pytest.approx(0.25)


def test_registry_property():
    engine = _engine()
    assert "dax" in engine.registry


def test_watch_candidate_without_analysis():
    engine = _engine()
    report = engine.discover(
        markets=["sp500"],
        symbol_source=make_symbol_source({"sp500": [make_symbol("XYZ", sector="Tech")]}),
    )
    assert report.opportunities[0].is_watch
