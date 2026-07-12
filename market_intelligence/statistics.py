"""Kennzahlen über alle bewerteten Chancen (reine Aggregation).

Fasst **bereits bewertete** Chancen zu objektiven Kennzahlen zusammen (Anzahlen,
Durchschnitte, häufigste Branchen/Märkte). Es entstehen **keine** neuen
Bewertungen – nur Aggregation vorhandener Werte.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from models.opportunity import Opportunity, OpportunityStatistics


def _average(values: Sequence[float]) -> float | None:
    """Durchschnitt einer Werteliste (oder ``None`` bei leerer Liste)."""
    return sum(values) / len(values) if values else None


def _top_counts(labels: Sequence[str], limit: int) -> tuple[tuple[str, int], ...]:
    """Häufigste, nicht-leere Labels als ``(Name, Anzahl)`` (absteigend)."""
    counter = Counter(label for label in labels if label)
    return tuple(counter.most_common(max(limit, 0)))


def compute_statistics(
    opportunities: Sequence[Opportunity], top_sectors: int = 5, top_markets: int = 5
) -> OpportunityStatistics:
    """Berechnet die Kennzahlen über alle Chancen (reine Aggregation)."""
    if not opportunities:
        return OpportunityStatistics()
    scores = [o.opportunity_score for o in opportunities]
    risks = [o.risk for o in opportunities if o.risk is not None]
    confidences = [o.confidence for o in opportunities]
    return OpportunityStatistics(
        analyzed_count=len(opportunities),
        long_count=sum(1 for o in opportunities if o.is_long),
        short_count=sum(1 for o in opportunities if o.is_short),
        watch_count=sum(1 for o in opportunities if o.is_watch),
        average_score=_average(scores),
        average_risk=_average(risks),
        average_confidence=_average(confidences),
        top_sectors=_top_counts([o.sector for o in opportunities], top_sectors),
        top_markets=_top_counts([o.market for o in opportunities], top_markets),
    )
