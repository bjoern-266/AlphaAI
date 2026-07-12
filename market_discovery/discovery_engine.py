"""Orchestrierung des Discovery-Ablaufs (reine Verkettung, keine Berechnung).

Verkettet Vorfilter → Kandidatenaufbau → **bestehenden** Market-Intelligence-
Schritt → Branchen-Ausgleich → Statistik zu einem
:class:`~models.market_discovery.DiscoveryReport`. Der Market-Intelligence-Schritt
wird **injiziert** (Duck-Typing ``analyze(candidates)``); dieses Modul importiert
**nichts** aus ``engines`` und **berechnet nichts** selbst.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from typing import Protocol

from market_discovery.candidate import build_market_candidate, to_discovery_opportunity
from market_discovery.candidate_filter import CandidateFilter, apply_filter
from market_discovery.market_statistics import compute_statistics
from market_discovery.sector_balancer import BalanceConfig, balance
from models.market_discovery import (
    CandidateAnalysis,
    DiscoveryOpportunity,
    DiscoveryReport,
    MarketSymbol,
    MarketUniverse,
)
from models.opportunity import MarketCandidate, OpportunityReport

# Injizierte Quelle der **bereits vorhandenen** Analyse-Ergebnisse je Wert.
AnalysisProvider = Callable[[MarketSymbol], CandidateAnalysis]


class IntelligenceEngine(Protocol):
    """Minimales Protokoll des Market-Intelligence-Schritts (Duck-Typing)."""

    def analyze(self, candidates: Sequence[MarketCandidate]) -> OpportunityReport: ...  # noqa: D102


def empty_analysis_provider(symbol: MarketSymbol) -> CandidateAnalysis:
    """Standard-Provider ohne Ergebnisse (echte Anbindung wird injiziert)."""
    return CandidateAnalysis()


def run_discovery(
    universe: MarketUniverse,
    candidate_filter: CandidateFilter,
    analysis_provider: AnalysisProvider,
    intelligence: IntelligenceEngine,
    balance_config: BalanceConfig,
    top_sectors: int,
    top_markets: int,
    warnings: list[str],
) -> DiscoveryReport:
    """Führt den Discovery-Ablauf aus und baut den Report (ohne Zeit/Cache)."""
    collected_warnings = list(warnings)
    valid = universe.size > 0
    if not valid:
        collected_warnings.append("Leeres Universum – der Report ist leer.")

    kept, rejected = apply_filter(universe.symbols, candidate_filter)
    symbol_by_ticker = {symbol.ticker: symbol for symbol in kept}
    candidates = [build_market_candidate(symbol, analysis_provider(symbol)) for symbol in kept]

    opportunity_report = intelligence.analyze(candidates)
    collected_warnings.extend(opportunity_report.warnings)

    balanced = balance(opportunity_report.opportunities, balance_config)
    discovery_opportunities: tuple[DiscoveryOpportunity, ...] = tuple(
        to_discovery_opportunity(opportunity, symbol_by_ticker.get(opportunity.ticker), index + 1)
        for index, opportunity in enumerate(balanced)
    )

    statistics = compute_statistics(
        universe_count=universe.size,
        rejected_count=len(rejected),
        opportunities=discovery_opportunities,
        top_sectors=top_sectors,
        top_markets=top_markets,
    )

    return DiscoveryReport(
        opportunities=discovery_opportunities,
        statistics=statistics,
        rejected=rejected,
        markets=universe.markets,
        valid=valid,
        warnings=collected_warnings,
        metadata={
            "universe_size": universe.size,
            "kept": len(kept),
            "rejected": len(rejected),
            "opportunities": len(discovery_opportunities),
        },
        timestamp=datetime.now(UTC),
    )
