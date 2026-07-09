"""Cache für Risk-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.risk.RiskReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.risk import RiskReport


class RiskCache(Cache[RiskReport]):
    """Größenbegrenzter Cache für Risk-Ergebnisse (FIFO)."""
