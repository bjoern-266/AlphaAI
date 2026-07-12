"""Reine Ranking-/Sortier-Bausteine für Chancen.

Diese Funktionen ordnen und sortieren **bereits bewertete** Chancen. Sie
**berechnen keine** Scores – sie arbeiten ausschließlich mit den vorhandenen
Werten der :class:`~models.opportunity.Opportunity`.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from models.opportunity import Opportunity
from models.recommendation import RecommendationStrength

# Unterstützte Sortierkriterien.
SORT_SCORE = "opportunity_score"
SORT_CONFIDENCE = "confidence"
SORT_RISK = "risk"
SORT_RECOMMENDATION = "recommendation"
SORT_ALPHABETICAL = "alphabetical"

SORT_CRITERIA = (SORT_SCORE, SORT_CONFIDENCE, SORT_RISK, SORT_RECOMMENDATION, SORT_ALPHABETICAL)

# Unterstützte Top-N-Größen.
TOP_SIZES = (5, 10, 20, 50)

# Rangordnung der Empfehlungsstärke (höher = stärker).
_STRENGTH_ORDER: dict[RecommendationStrength, int] = {
    RecommendationStrength.VERY_HIGH: 5,
    RecommendationStrength.HIGH: 4,
    RecommendationStrength.MEDIUM: 3,
    RecommendationStrength.LOW: 2,
    RecommendationStrength.REJECT: 1,
}


def strength_rank(strength: RecommendationStrength) -> int:
    """Gibt die numerische Rangordnung einer Empfehlungsstärke zurück."""
    return _STRENGTH_ORDER.get(strength, 0)


def _sort_key(opportunity: Opportunity, criterion: str):  # noqa: ANN202 - interner Sortierschlüssel
    """Bildet den Sortierschlüssel einer Chance für ein Kriterium."""
    if criterion == SORT_CONFIDENCE:
        return opportunity.confidence
    if criterion == SORT_RISK:
        # Fehlt der Risiko-Faktor, ans Ende sortieren (neutralster Wert).
        return opportunity.risk if opportunity.risk is not None else -1.0
    if criterion == SORT_RECOMMENDATION:
        return strength_rank(opportunity.recommendation_strength)
    if criterion == SORT_ALPHABETICAL:
        return opportunity.ticker
    return opportunity.opportunity_score


def sort_opportunities(
    opportunities: Sequence[Opportunity], criterion: str = SORT_SCORE, descending: bool = True
) -> tuple[Opportunity, ...]:
    """Sortiert Chancen stabil nach einem Kriterium (Standard: Score absteigend).

    Alphabetisch wird immer aufsteigend sortiert (A→Z), unabhängig von
    ``descending``.
    """
    if criterion == SORT_ALPHABETICAL:
        return tuple(sorted(opportunities, key=lambda o: o.ticker))
    return tuple(sorted(opportunities, key=lambda o: _sort_key(o, criterion), reverse=descending))


def assign_ranks(opportunities: Sequence[Opportunity]) -> tuple[Opportunity, ...]:
    """Vergibt fortlaufende Ränge (1..N) in der gegebenen Reihenfolge."""
    return tuple(
        replace(opportunity, opportunity_rank=index + 1)
        for index, opportunity in enumerate(opportunities)
    )


def top(opportunities: Sequence[Opportunity], size: int) -> tuple[Opportunity, ...]:
    """Gibt die ersten ``size`` Chancen zurück (reine Auswahl, keine Berechnung)."""
    return tuple(opportunities[: max(size, 0)])
