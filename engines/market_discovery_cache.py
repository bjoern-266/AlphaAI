"""Cache für Discovery-Ergebnisse (Re-Export).

Die Definition liegt im Subsystem :mod:`market_discovery.discovery_cache`. Dieses
Modul re-exportiert sie unter dem etablierten Pfad
``engines.market_discovery_cache`` – konsistent mit
``engines.market_intelligence_cache``.
"""

from __future__ import annotations

from market_discovery.discovery_cache import DiscoveryCache

__all__ = ["DiscoveryCache"]
