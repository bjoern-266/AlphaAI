"""Live-Verdrahtung: echte Marktdaten → Pipeline → Market Intelligence.

Dieses Modul ist ein **Composition Root** für den produktiven Betrieb mit echten
Marktdaten. Es verbindet die **unveränderten** bestehenden Bausteine:

    Marktdaten (MarketDataEngine / Yahoo-Provider)
        → Analyse-Pipeline (IntegrationRunner: Indicator→…→Recommendation)
        → Market Intelligence (Priorisierung zu einem OpportunityReport)

Es enthält **keine** neue Fachlogik, berechnet nichts selbst und trifft **keine**
Handelsentscheidung – es reicht die Ausgaben der bestehenden Engines nur weiter.
Der Datenprovider ist injizierbar (Standard: Yahoo). Für Tests/Offline-Betrieb
kann ein synthetischer Provider übergeben werden.

Verwendung als Report-Quelle des Hintergrunddienstes::

    live = LiveBackend.from_config()
    report_sources = {"opportunities": live.opportunity_report}
"""

from __future__ import annotations

from collections.abc import Sequence

from core.config import Settings, load_settings
from core.logging_config import get_logger
from data.market_data_engine import MarketDataEngine
from data.market_result import MarketResult
from engines.market_intelligence_engine import MarketIntelligenceEngine
from models.opportunity import MarketCandidate, OpportunityReport
from models.recommendation import RecommendationResult
from pipeline.runner import IntegrationRunner
from providers.base_provider import BaseProvider
from repositories.repository_factory import build_repository

_logger = get_logger(__name__)


class LiveBackend:
    """Erzeugt aus echten Marktdaten priorisierte Chancen (OpportunityReport).

    Args:
        settings: Geladene Projektkonfiguration.
        market_engine: Zugriffsschicht auf Marktdaten (Data Layer).
        runner: Vollständige Analyse-Pipeline (unverändert).
        intelligence: Market-Intelligence-Engine (Priorisierung).
    """

    def __init__(
        self,
        settings: Settings,
        market_engine: MarketDataEngine,
        runner: IntegrationRunner,
        intelligence: MarketIntelligenceEngine,
    ) -> None:
        self._settings = settings
        self._market = market_engine
        self._runner = runner
        self._intelligence = intelligence

    @classmethod
    def from_config(cls, provider: BaseProvider | None = None) -> LiveBackend:
        """Baut die Live-Verdrahtung aus den Konfigurations-/Regeldateien.

        Args:
            provider: Optionaler Datenprovider (Standard: der in der Konfiguration
                hinterlegte, i. d. R. Yahoo). Für Tests/Offline injizierbar.
        """
        settings = load_settings()
        repository = build_repository(settings, provider=provider)
        return cls(
            settings=settings,
            market_engine=MarketDataEngine(repository, settings),
            runner=IntegrationRunner.from_config(),
            intelligence=MarketIntelligenceEngine.from_config(),
        )

    def opportunity_report(
        self,
        symbols: Sequence[str] | None = None,
        market: str = "watchlist",
    ) -> OpportunityReport:
        """Lädt Daten, führt die Pipeline aus und priorisiert die Chancen.

        Args:
            symbols: Zu analysierende Symbole (Standard: ``[markets].symbols`` aus
                der Konfiguration).
            market: Anzeigename/Universumsbezeichnung für die Chancen.

        Returns:
            Ein priorisierter :class:`OpportunityReport` (unverändert aus den
            bestehenden Engines zusammengesetzt).
        """
        chosen = tuple(symbols) if symbols else tuple(self._settings.markets)
        result = self._market.get_symbols(chosen, market=market)
        candidates = [self._candidate(result, symbol, market) for symbol in chosen]
        report = self._intelligence.analyze(candidates)
        _logger.info(
            "Live-Analyse: %d Symbole → %d Chancen.", len(chosen), len(report.opportunities)
        )
        return report

    def _candidate(self, result: MarketResult, symbol: str, market: str) -> MarketCandidate:
        """Führt die Pipeline für ein Symbol aus und baut den Kandidaten."""
        pipeline = self._runner.run(result, symbol)
        recommendation = _best_recommendation(pipeline.recommendations.results)
        return MarketCandidate(
            ticker=symbol,
            company=symbol,
            market=market,
            recommendation=recommendation,
        )


def _best_recommendation(
    results: Sequence[RecommendationResult],
) -> RecommendationResult | None:
    """Wählt die Empfehlung mit der höchsten Gesamtbewertung (oder ``None``)."""
    valid = [result for result in results if result is not None]
    if not valid:
        return None
    return max(valid, key=lambda result: result.overall_rating)


__all__ = ["LiveBackend"]
