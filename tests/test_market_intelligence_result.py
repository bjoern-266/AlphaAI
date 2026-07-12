"""Tests des Re-Exports der Market-Intelligence-Ergebnistypen."""

from __future__ import annotations

from engines import market_intelligence_result as result
from models import opportunity as models_opportunity


def test_reexports_opportunity_report():
    assert result.OpportunityReport is models_opportunity.OpportunityReport


def test_reexports_opportunity():
    assert result.Opportunity is models_opportunity.Opportunity


def test_reexports_candidate():
    assert result.MarketCandidate is models_opportunity.MarketCandidate


def test_reexports_context():
    assert result.MarketIntelligenceContext is models_opportunity.MarketIntelligenceContext


def test_reexports_statistics():
    assert result.OpportunityStatistics is models_opportunity.OpportunityStatistics


def test_reexports_explanation():
    assert result.OpportunityExplanation is models_opportunity.OpportunityExplanation


def test_reexports_watchlist():
    assert result.Watchlist is models_opportunity.Watchlist


def test_reexports_model_output():
    assert result.OpportunityModelOutput is models_opportunity.OpportunityModelOutput


def test_all_names_exported():
    for name in result.__all__:
        assert hasattr(result, name)
