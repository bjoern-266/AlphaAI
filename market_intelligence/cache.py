"""Cache für Market-Intelligence-Ergebnisse.

Dünne Spezialisierung des generischen :class:`core.cache.Cache` auf
:class:`~models.opportunity.OpportunityReport`. Das Verhalten (FIFO-Verdrängung,
Treffer-/Fehltrefferzählung, ``get``/``set``/``clear``/``len``) stammt
vollständig aus der generischen Basis.
"""

from __future__ import annotations

from core.cache import Cache
from models.opportunity import OpportunityReport


class OpportunityCache(Cache[OpportunityReport]):
    """Größenbegrenzter Cache für Opportunity-Reports (FIFO)."""
