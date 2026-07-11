"""Cache für Analytics-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.analytics.AnalyticsReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.analytics import AnalyticsReport


class AnalyticsCache(Cache[AnalyticsReport]):
    """Größenbegrenzter Cache für Analytics-Ergebnisse (FIFO)."""
