"""Kennzahlen eines Discovery-Laufs (reine Aggregation).

Fasst die **bereits bewerteten** Chancen sowie die Universum-/Vorfilter-Zahlen zu
objektiven Kennzahlen zusammen. Es entstehen **keine** neuen Bewertungen.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence

from models.market_discovery import DiscoveryOpportunity, DiscoveryStatistics


def _average(values: Sequence[float]) -> float | None:
    """Durchschnitt einer Werteliste (oder ``None`` bei leerer Liste)."""
    return sum(values) / len(values) if values else None


def _top_counts(labels: Sequence[str], limit: int) -> tuple[tuple[str, int], ...]:
    """Häufigste, nicht-leere Labels als ``(Name, Anzahl)`` (absteigend)."""
    counter = Counter(label for label in labels if label)
    return tuple(counter.most_common(max(limit, 0)))


def compute_statistics(
    universe_count: int,
    rejected_count: int,
    opportunities: Sequence[DiscoveryOpportunity],
    top_sectors: int = 5,
    top_markets: int = 5,
) -> DiscoveryStatistics:
    """Berechnet die Kennzahlen des Discovery-Laufs (reine Aggregation)."""
    scores = [o.opportunity_score for o in opportunities]
    risks = [o.risk for o in opportunities if o.risk is not None]
    confidences = [o.confidence for o in opportunities]
    return DiscoveryStatistics(
        universe_count=universe_count,
        rejected_count=rejected_count,
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
