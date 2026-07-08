"""Market Structure – Gesamtzustand der Struktur aus BOS/CHoCH.

Fasst die erkannten Struktur-Brüche zu einem aktuellen Strukturzustand
zusammen (Richtung des jüngsten Bruchs, Anzahl BOS/CHoCH). Nutzt den
gemeinsamen Struktur-Helper und ist damit unabhängig von den übrigen Mustern.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from patterns.base import (
    BasePattern,
    PatternDetection,
    PatternDirection,
    PatternResult,
    PatternType,
    detect_structure_breaks,
    require_int,
)


class MarketStructurePattern(BasePattern):
    """Detektor für den aktuellen Marktstruktur-Zustand."""

    name = "market_structure"
    pattern_type = PatternType.MARKET_STRUCTURE

    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Benötigt genug Kerzen, um Swings zu bestätigen."""
        return 2 * require_int(params, "swing_lookback", self.name) + 1

    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Erzeugt eine Zusammenfassung des aktuellen Strukturzustands."""
        lookback = require_int(params, "swing_lookback", self.name)
        detection = PatternDetection()
        events = detect_structure_breaks(data, lookback)

        bos_count = sum(1 for e in events if e.kind == "bos")
        choch_count = sum(1 for e in events if e.kind == "choch")

        if not events:
            detection.warnings.append("Keine Struktur-Brüche erkannt.")
            detection.patterns.append(
                PatternResult(
                    name=self.name,
                    pattern_type=self.pattern_type,
                    direction=PatternDirection.NEUTRAL,
                    strength=0.0,
                    confidence=0.3,
                    timestamp=data.index[-1],
                    price_level=float(data["close"].iloc[-1]),
                    metadata={"bos_count": 0, "choch_count": 0, "last_break": None},
                )
            )
            return detection

        last = events[-1]
        detection.patterns.append(
            PatternResult(
                name=self.name,
                pattern_type=self.pattern_type,
                direction=last.direction,
                strength=float(min(100.0, len(events) * 20.0)),
                confidence=0.6,
                timestamp=last.timestamp,
                price_level=last.level,
                metadata={
                    "bos_count": bos_count,
                    "choch_count": choch_count,
                    "last_break": last.kind,
                    "event_count": len(events),
                },
            )
        )
        return detection
