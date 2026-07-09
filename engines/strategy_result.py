"""Ergebnistypen der Strategy Engine (Re-Export).

Die Definitionen liegen seit Sprint 7.5 in der Entities-Schicht
:mod:`models.strategy`. Dieses Modul re-exportiert sie unter dem etablierten
Pfad ``engines.strategy_result`` zur Rückwärtskompatibilität.
"""

from __future__ import annotations

from models.strategy import StrategyDirection, StrategyReport, StrategyResult

__all__ = ["StrategyResult", "StrategyDirection", "StrategyReport"]
