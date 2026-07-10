"""Cache für Paper-Trading-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.paper_trading.PaperTradingReport`. Das Verhalten (FIFO-
Verdrängung, Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``)
stammt vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.paper_trading import PaperTradingReport


class PaperTradingCache(Cache[PaperTradingReport]):
    """Größenbegrenzter Cache für Paper-Trading-Ergebnisse (FIFO)."""
