"""Ergebnistypen der Pattern Engine (Re-Export).

Die Definitionen liegen seit Sprint 7.5 in der Entities-Schicht
:mod:`models.pattern`. Dieses Modul re-exportiert sie unter dem etablierten
Pfad ``engines.pattern_result`` zur Rückwärtskompatibilität.
"""

from __future__ import annotations

from models.pattern import PatternDirection, PatternReport, PatternResult, PatternType

__all__ = ["PatternResult", "PatternType", "PatternDirection", "PatternReport"]
