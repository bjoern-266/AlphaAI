"""Cache für Operations-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.operations.OperationReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.operations import OperationReport


class OperationsCache(Cache[OperationReport]):
    """Größenbegrenzter Cache für Operation-Reports (FIFO)."""
