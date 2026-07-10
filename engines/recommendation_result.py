"""Ergebnistypen der Recommendation Engine (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.recommendation`.
Dieses Modul re-exportiert sie unter dem etablierten Pfad
``engines.recommendation_result`` – konsistent mit ``engines.risk_result`` usw.
"""

from __future__ import annotations

from models.recommendation import (
    RECOMMENDATION_FACTOR_NAMES,
    Direction,
    RecommendationContext,
    RecommendationFactor,
    RecommendationModelOutput,
    RecommendationReport,
    RecommendationResult,
    RecommendationStrength,
    SuggestedAction,
)

__all__ = [
    "RecommendationResult",
    "RecommendationReport",
    "Direction",
    "RecommendationStrength",
    "SuggestedAction",
    "RecommendationFactor",
    "RecommendationModelOutput",
    "RecommendationContext",
    "RECOMMENDATION_FACTOR_NAMES",
]
