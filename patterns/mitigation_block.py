"""Mitigation Block – vorbereitet, noch keine Erkennung.

Der Detektor ist registriert und dokumentiert, erkennt aber bewusst noch keine
Muster (``implemented = False``). Die Erkennung folgt in einem späteren Sprint.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from patterns.base import BasePattern, PatternDetection, PatternType


class MitigationBlockPattern(BasePattern):
    """Vorbereiteter Mitigation-Block-Detektor (ohne Erkennung)."""

    name = "mitigation_block"
    pattern_type = PatternType.MITIGATION_BLOCK
    implemented = False

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Platzhalter-Bedarf, bis die Erkennung implementiert ist."""
        return 1

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Liefert bewusst keine Muster (vorbereitet)."""
        return PatternDetection(
            warnings=["Mitigation Block: vorbereitet, noch nicht implementiert."]
        )
