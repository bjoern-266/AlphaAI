"""Ergebnistypen des Paper-Trading-Frameworks (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.paper_trading`.
Dieses Modul re-exportiert sie unter dem etablierten Pfad
``engines.paper_trading_result`` – konsistent mit ``engines.backtest_result`` usw.
"""

from __future__ import annotations

from models.paper_trading import (
    CloseReason,
    JournalEntry,
    OrderAction,
    PaperEquityPoint,
    PaperOrder,
    PaperPerformance,
    PaperPosition,
    PaperStatistics,
    PaperTrade,
    PaperTradingContext,
    PaperTradingModelOutput,
    PaperTradingReport,
    PaperTradingResult,
    PositionStatus,
)

__all__ = [
    "PaperTradingResult",
    "PaperTradingReport",
    "PaperTradingContext",
    "PaperTradingModelOutput",
    "PaperPosition",
    "PaperOrder",
    "PaperTrade",
    "JournalEntry",
    "PaperEquityPoint",
    "PaperStatistics",
    "PaperPerformance",
    "OrderAction",
    "PositionStatus",
    "CloseReason",
]
