"""Cache für Discovery-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.market_discovery.DiscoveryReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.market_discovery import DiscoveryReport


class DiscoveryCache(Cache[DiscoveryReport]):
    """Größenbegrenzter Cache für Discovery-Reports (FIFO)."""
