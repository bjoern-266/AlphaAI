"""Ergebnistypen der Score Engine (Re-Export).

Die Definitionen liegen seit Sprint 7.5 in der Entities-Schicht
:mod:`models.score`. Dieses Modul re-exportiert sie unter dem etablierten Pfad
``engines.score_result`` zur Rückwärtskompatibilität.
"""

from __future__ import annotations

from models.score import ScoreReport, ScoreResult

__all__ = ["ScoreResult", "ScoreReport"]
