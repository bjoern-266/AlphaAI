"""Ergebnisobjekt für Marktdaten (Re-Export).

Die Definitionen (kanonisches Spaltenschema, :class:`MarketStatus`,
:class:`MarketResult`) liegen seit Sprint 7.5 in der Entities-Schicht
:mod:`models.market`. Dieses Modul re-exportiert sie unter dem etablierten Pfad
``data.market_result`` zur Rückwärtskompatibilität.
"""

from __future__ import annotations

from models.market import (
    COL_ADJ_CLOSE,
    COL_CLOSE,
    COL_HIGH,
    COL_LOW,
    COL_OPEN,
    COL_VOLUME,
    OHLCV_COLUMNS,
    MarketResult,
    MarketStatus,
)

__all__ = [
    "COL_OPEN",
    "COL_HIGH",
    "COL_LOW",
    "COL_CLOSE",
    "COL_ADJ_CLOSE",
    "COL_VOLUME",
    "OHLCV_COLUMNS",
    "MarketStatus",
    "MarketResult",
]
