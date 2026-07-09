"""Cache für Score-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.score.ScoreReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.score import ScoreReport


class ScoreCache(Cache[ScoreReport]):
    """Größenbegrenzter Cache für Score-Ergebnisse (FIFO)."""
