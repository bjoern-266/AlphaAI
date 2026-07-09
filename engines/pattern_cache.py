"""Cache für erkannte Muster.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.pattern.PatternReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.pattern import PatternReport


class PatternCache(Cache[PatternReport]):
    """Größenbegrenzter Cache für Pattern-Ergebnisse (FIFO)."""
