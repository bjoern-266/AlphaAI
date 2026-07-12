"""End-to-End-Szenarien des Market-Discovery-Frameworks.

Prüft die vollständige Kette: Universum laden → Vorfilter → (injizierte)
vorhandene Ergebnisse → Market-Intelligence → Branchen-Ausgleich → Statistik →
DiscoveryReport. Der Benutzer gibt keine Aktien vor; die Engine durchsucht den
konfigurierten Markt selbst.
"""

from __future__ import annotations

import pytest

from engines.market_discovery_engine import MarketDiscoveryEngine
from engines.market_intelligence_engine import MarketIntelligenceEngine
from models.recommendation import Direction, RecommendationStrength
from tests.market_discovery_helpers import (
    make_analysis,
    make_analysis_provider,
    make_symbol,
    make_symbol_source,
)

# Ein gemischtes Universum mit Halbleiter-Häufung (für den Branchen-Ausgleich).
_UNIVERSE = {
    "sp500": [
        make_symbol("NVDA", company="Nvidia", sector="Semiconductors", market="sp500"),
        make_symbol("AMD", company="AMD", sector="Semiconductors", market="sp500"),
        make_symbol("AVGO", company="Broadcom", sector="Semiconductors", market="sp500"),
        make_symbol("AAPL", company="Apple", sector="Tech", market="sp500"),
        make_symbol("JPM", company="JPMorgan", sector="Finance", market="sp500"),
        make_symbol("PENNY", company="Junk", sector="Junk", market="sp500", price=0.3),
        make_symbol(
            "THIN", company="Thin", sector="Tech", market="sp500", average_dollar_volume=1000.0
        ),
    ],
    "dax": [
        make_symbol("SAP", company="SAP", sector="Software", country="DE", market="dax"),
    ],
}

_ANALYSES = {
    "NVDA": make_analysis("NVDA", Direction.LONG, RecommendationStrength.VERY_HIGH, 95.0, 85.0),
    "AMD": make_analysis("AMD", Direction.LONG, RecommendationStrength.VERY_HIGH, 92.0, 80.0),
    "AVGO": make_analysis("AVGO", Direction.LONG, RecommendationStrength.HIGH, 90.0, 78.0),
    "AAPL": make_analysis("AAPL", Direction.LONG, RecommendationStrength.HIGH, 80.0, 70.0),
    "JPM": make_analysis("JPM", Direction.SHORT, RecommendationStrength.MEDIUM, 60.0, 55.0),
    "SAP": make_analysis("SAP", Direction.SHORT, RecommendationStrength.HIGH, 75.0, 65.0),
}


@pytest.fixture(scope="module")
def report():
    engine = MarketDiscoveryEngine.from_config(intelligence=MarketIntelligenceEngine.from_config())
    return engine.discover(
        markets=["sp500", "dax"],
        symbol_source=make_symbol_source(_UNIVERSE),
        analysis_provider=make_analysis_provider(_ANALYSES),
    )


def test_report_valid(report):
    assert report.valid is True


def test_universe_and_rejections(report):
    assert report.statistics.universe_count == 8
    # PENNY (Penny) + THIN (Liquidität) werden verworfen.
    assert report.statistics.rejected_count == 2
    assert report.statistics.analyzed_count == 6


def test_ranks_contiguous(report):
    assert [o.rank for o in report.opportunities] == list(range(1, 7))


def test_no_user_watchlist_needed(report):
    # Alle Werte stammen aus dem geladenen Universum, nicht aus einer Vorgabe.
    tickers = {o.ticker for o in report.opportunities}
    assert tickers == {"NVDA", "AMD", "AVGO", "AAPL", "JPM", "SAP"}


def test_sector_balancing_breaks_semiconductor_streak(report):
    # Drei Halbleiter (NVDA, AMD, AVGO) sind am stärksten; der Ausgleich (max_streak=2)
    # zieht spätestens nach zwei Halbleitern eine andere Branche vor.
    sectors = [o.sector for o in report.opportunities]
    # Keine drei gleichen Branchen direkt hintereinander.
    for i in range(len(sectors) - 2):
        assert not (sectors[i] == sectors[i + 1] == sectors[i + 2])


def test_top_sectors_leads_with_semiconductors(report):
    assert report.statistics.top_sectors[0] == ("Semiconductors", 3)


def test_countries_present(report):
    assert report.by_ticker("SAP").country == "DE"
    assert report.by_ticker("AAPL").country == "US"


def test_direction_counts(report):
    assert report.statistics.long_count == 4
    assert report.statistics.short_count == 2


def test_top_selection(report):
    assert len(report.top(3)) == 3


def test_scores_within_bounds(report):
    for opportunity in report.opportunities:
        assert 0.0 <= opportunity.opportunity_score <= 100.0


def test_determinism(report):
    again = MarketDiscoveryEngine.from_config().discover(
        markets=["sp500", "dax"],
        symbol_source=make_symbol_source(_UNIVERSE),
        analysis_provider=make_analysis_provider(_ANALYSES),
    )
    assert [o.ticker for o in again.opportunities] == [o.ticker for o in report.opportunities]


def test_rejected_carries_reason(report):
    reasons = {r.ticker: r.reason for r in report.rejected}
    assert reasons["PENNY"] == "Penny Stock"
    assert reasons["THIN"] == "Liquidität zu gering"


def test_markets_recorded(report):
    assert set(report.markets) == {"sp500", "dax"}
