"""Antwort-Cache der REST-API (typisierte Ableitung der generischen Basis).

Der :class:`ApplicationCache` speichert fertige API-Antworten
(:class:`~application.api.router.ApiResponse`) unter einem vom Aufrufer
gebildeten Schlüssel. Er erbt das gesamte Verhalten (``get``/``set``/``clear``/
``hits``/``misses``/``len``) von der generischen :class:`core.cache.Cache` und
legt lediglich den Wertetyp fest – konsistent mit den übrigen Engine-Caches.
"""

from __future__ import annotations

from application.api.router import ApiResponse
from core.cache import Cache


class ApplicationCache(Cache[ApiResponse]):
    """Größenbegrenzter Cache für API-Antworten (FIFO-Verdrängung)."""


__all__ = ["ApplicationCache"]
