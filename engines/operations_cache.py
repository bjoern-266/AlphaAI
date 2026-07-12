"""Cache für Operations-Ergebnisse (Re-Export).

Die Definition liegt im Subsystem :mod:`operations.operations_cache`. Dieses
Modul re-exportiert sie unter dem etablierten Pfad ``engines.operations_cache`` –
konsistent mit ``engines.market_discovery_cache``.
"""

from __future__ import annotations

from operations.operations_cache import OperationsCache

__all__ = ["OperationsCache"]
