"""Cache für Recommendation-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.recommendation.RecommendationReport`. Das Verhalten
(FIFO-Verdrängung, Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/
``len``) stammt vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.recommendation import RecommendationReport


class RecommendationCache(Cache[RecommendationReport]):
    """Größenbegrenzter Cache für Recommendation-Ergebnisse (FIFO)."""
