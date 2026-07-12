"""Tests der Market-Discovery-Modelle (unveränderlich, keine Berechnung)."""

from __future__ import annotations

import dataclasses

import pytest

from models.market_discovery import (
    CandidateAnalysis,
    DiscoveryReport,
    DiscoveryStatistics,
    MarketDefinition,
    MarketSymbol,
    MarketUniverse,
    RejectedCandidate,
)
from models.recommendation import Direction
from tests.market_discovery_helpers import make_discovery_opportunity, make_symbol


def test_market_definition_defaults():
    definition = MarketDefinition(name="dax")
    assert definition.title == ""
    assert definition.country == ""


def test_market_symbol_defaults():
    symbol = MarketSymbol(ticker="AAPL")
    assert symbol.tradable is True
    assert symbol.delisted is False
    assert symbol.price is None
    assert symbol.metadata == {}


def test_market_symbol_is_frozen():
    symbol = make_symbol()
    with pytest.raises(dataclasses.FrozenInstanceError):
        symbol.ticker = "X"  # type: ignore[misc]


def test_universe_size_and_tickers():
    universe = MarketUniverse(symbols=(make_symbol("A"), make_symbol("B")))
    assert universe.size == 2
    assert universe.tickers() == ("A", "B")


def test_universe_by_market():
    universe = MarketUniverse(
        symbols=(make_symbol("A", market="dax"), make_symbol("B", market="sp500"))
    )
    assert [s.ticker for s in universe.by_market("dax")] == ["A"]


def test_candidate_analysis_defaults():
    analysis = CandidateAnalysis()
    assert analysis.recommendation is None
    assert analysis.analytics is None


def test_rejected_candidate():
    rejected = RejectedCandidate(ticker="X", reason="Penny Stock")
    assert rejected.reason == "Penny Stock"


def test_discovery_opportunity_direction_properties():
    long_o = make_discovery_opportunity(direction=Direction.LONG)
    short_o = make_discovery_opportunity(direction=Direction.SHORT)
    watch_o = make_discovery_opportunity(direction=Direction.NEUTRAL)
    assert long_o.is_long
    assert short_o.is_short
    assert watch_o.is_watch


def test_discovery_opportunity_is_frozen():
    opportunity = make_discovery_opportunity()
    with pytest.raises(dataclasses.FrozenInstanceError):
        opportunity.rank = 5  # type: ignore[misc]


def test_statistics_defaults():
    stats = DiscoveryStatistics()
    assert stats.universe_count == 0
    assert stats.average_score is None
    assert stats.top_sectors == ()


def test_report_defaults():
    report = DiscoveryReport()
    assert report.opportunities == ()
    assert report.opportunity_count == 0
    assert report.valid is True


def test_report_top():
    opps = tuple(make_discovery_opportunity(ticker=f"T{i}", rank=i + 1) for i in range(5))
    report = DiscoveryReport(opportunities=opps)
    assert len(report.top(3)) == 3
    assert report.top(0) == ()


def test_report_by_ticker():
    opps = (make_discovery_opportunity("A"), make_discovery_opportunity("B"))
    report = DiscoveryReport(opportunities=opps)
    assert report.by_ticker("B").ticker == "B"
    assert report.by_ticker("Z") is None


def test_report_is_frozen():
    report = DiscoveryReport()
    with pytest.raises(dataclasses.FrozenInstanceError):
        report.valid = False  # type: ignore[misc]


def test_universe_empty_defaults():
    universe = MarketUniverse()
    assert universe.size == 0
    assert universe.tickers() == ()
