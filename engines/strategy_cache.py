"""Cache für Strategie-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.strategy.StrategyReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.strategy import StrategyReport


class StrategyCache(Cache[StrategyReport]):
    """Größenbegrenzter Cache für Strategie-Ergebnisse (FIFO)."""
