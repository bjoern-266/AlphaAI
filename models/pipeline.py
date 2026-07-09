"""Domänenmodell: Ergebnis eines vollständigen Analyse-Durchlaufs.

:class:`PipelineResult` bündelt die Ausgaben **aller** Stufen der
AlphaAI-Entscheidungskette für ein Symbol:

``MarketResult → IndicatorResult → PatternReport → StrategyReport →
ScoreReport → RiskReport → RecommendationReport``

Teil der Entities-Schicht (``models/``). Es importiert ausschließlich andere
Modelle – **kein** Import aus ``engines``, ``pipeline`` o. Ä. Der eigentliche
Ablauf (Engine → Engine) liegt im :class:`pipeline.runner.IntegrationRunner`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from models.indicator import IndicatorResult
from models.market import MarketResult
from models.pattern import PatternReport
from models.recommendation import RecommendationReport, RecommendationResult
from models.risk import RiskReport
from models.score import ScoreReport
from models.strategy import StrategyReport


@dataclass(frozen=True, slots=True)
class PipelineResult:
    """Ergebnis eines End-to-End-Durchlaufs für **ein** Symbol (unveränderlich).

    Attributes:
        symbol: Analysiertes Symbol.
        timeframe: Zeitebenen-Label.
        market: Eingangs-Marktdaten (Data Layer).
        indicators: Ergebnis der Indicator Engine.
        patterns: Ergebnis der Pattern Engine.
        strategies: Ergebnis der Strategy Engine.
        scores: Ergebnis der Score Engine.
        risks: Ergebnis der Risk Engine.
        recommendations: Ergebnis der Recommendation Engine.
        warnings: Über alle Stufen gesammelte Warnungen.
        metadata: Zusatzinformationen (u. a. Stufen-Zählungen).
    """

    symbol: str
    timeframe: str
    market: MarketResult
    indicators: IndicatorResult
    patterns: PatternReport
    strategies: StrategyReport
    scores: ScoreReport
    risks: RiskReport
    recommendations: RecommendationReport
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def recommendation_count(self) -> int:
        """Anzahl erzeugter Empfehlungen."""
        return self.recommendations.recommendation_count

    def best(self) -> RecommendationResult | None:
        """Höchstbewertete Empfehlung (reine Anzeige, keine Handelsentscheidung)."""
        top = self.recommendations.top(1)
        return top[0] if top else None
