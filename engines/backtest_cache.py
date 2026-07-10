"""Cache für Backtest-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.backtest.BacktestReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.backtest import BacktestReport


class BacktestCache(Cache[BacktestReport]):
    """Größenbegrenzter Cache für Backtest-Ergebnisse (FIFO)."""
