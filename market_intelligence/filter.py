"""Filter für Chancen (reine Auswahl bereits bewerteter Chancen).

Die Filter schränken eine Menge von :class:`~models.opportunity.Opportunity` ein.
Sie **berechnen nichts** – sie wählen anhand vorhandener Werte aus (Richtung,
Risiko, Confidence, Empfehlungsstärke, Markt, Branche, Börse).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from market_intelligence.ranking import strength_rank
from models.opportunity import Opportunity
from models.recommendation import Direction, RecommendationStrength

# Richtungs-/Auswahlkennungen.
DIRECTION_LONG = "long"
DIRECTION_SHORT = "short"
DIRECTION_WATCH = "watch"

_DIRECTION_MAP = {
    DIRECTION_LONG: Direction.LONG,
    DIRECTION_SHORT: Direction.SHORT,
    DIRECTION_WATCH: Direction.NEUTRAL,
}


@dataclass(frozen=True, slots=True)
class OpportunityFilter:
    """Beschreibung eines Anzeige-Filters (unveränderlich).

    Alle Felder sind optional; nicht gesetzte Felder schränken nicht ein.

    Attributes:
        direction: ``"long"``/``"short"``/``"watch"`` oder ``None`` (alle).
        min_confidence: Minimale Confidence (0..1) oder ``None``.
        max_risk: Maximal zulässiges Risiko (0..100) oder ``None``. Chancen ohne
            Risiko-Faktor werden bei gesetztem Filter ausgeschlossen.
        min_strength: Minimale Empfehlungsstärke oder ``None``.
        market: Exakter Markt oder ``None``.
        sector: Exakte Branche oder ``None``.
        exchange: Exakte Börse oder ``None``.
    """

    direction: str | None = None
    min_confidence: float | None = None
    max_risk: float | None = None
    min_strength: RecommendationStrength | None = None
    market: str | None = None
    sector: str | None = None
    exchange: str | None = None

    def matches(self, opportunity: Opportunity) -> bool:
        """Prüft, ob eine Chance alle gesetzten Kriterien erfüllt."""
        if self.direction is not None:
            wanted = _DIRECTION_MAP.get(self.direction)
            if wanted is None or opportunity.direction is not wanted:
                return False
        if self.min_confidence is not None and opportunity.confidence < self.min_confidence:
            return False
        if self.max_risk is not None:
            if opportunity.risk is None or opportunity.risk > self.max_risk:
                return False
        if self.min_strength is not None and strength_rank(
            opportunity.recommendation_strength
        ) < strength_rank(self.min_strength):
            return False
        if self.market is not None and opportunity.market != self.market:
            return False
        if self.sector is not None and opportunity.sector != self.sector:
            return False
        if self.exchange is not None and opportunity.exchange != self.exchange:
            return False
        return True


def apply_filter(
    opportunities: Sequence[Opportunity], opportunity_filter: OpportunityFilter
) -> tuple[Opportunity, ...]:
    """Wendet einen :class:`OpportunityFilter` auf die Chancen an (Reihenfolge bleibt)."""
    return tuple(o for o in opportunities if opportunity_filter.matches(o))


def filter_by_direction(
    opportunities: Sequence[Opportunity], direction: str
) -> tuple[Opportunity, ...]:
    """Filtert nach ``"long"``/``"short"``/``"watch"``."""
    return apply_filter(opportunities, OpportunityFilter(direction=direction))


def filter_by_min_confidence(
    opportunities: Sequence[Opportunity], min_confidence: float
) -> tuple[Opportunity, ...]:
    """Filtert nach minimaler Confidence (0..1)."""
    return apply_filter(opportunities, OpportunityFilter(min_confidence=min_confidence))


def filter_by_max_risk(
    opportunities: Sequence[Opportunity], max_risk: float
) -> tuple[Opportunity, ...]:
    """Filtert nach maximalem Risiko (0..100)."""
    return apply_filter(opportunities, OpportunityFilter(max_risk=max_risk))


def filter_by_min_strength(
    opportunities: Sequence[Opportunity], min_strength: RecommendationStrength
) -> tuple[Opportunity, ...]:
    """Filtert nach minimaler Empfehlungsstärke."""
    return apply_filter(opportunities, OpportunityFilter(min_strength=min_strength))
