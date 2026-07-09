"""Cache für berechnete Indikatorergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.indicator.IndicatorResult`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.indicator import IndicatorResult


class IndicatorCache(Cache[IndicatorResult]):
    """Größenbegrenzter Cache für Indikatorergebnisse (FIFO)."""
