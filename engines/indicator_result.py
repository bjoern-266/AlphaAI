"""Ergebnistyp der Indicator Engine (Re-Export).

Die Definition von :class:`IndicatorResult` liegt seit Sprint 7.5 in der
Entities-Schicht :mod:`models.indicator`. Dieses Modul re-exportiert sie unter
dem etablierten Pfad ``engines.indicator_result`` zur Rückwärtskompatibilität.
"""

from __future__ import annotations

from models.indicator import IndicatorOutput, IndicatorResult

__all__ = ["IndicatorResult", "IndicatorOutput"]
