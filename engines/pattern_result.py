"""Ergebnistypen der Pattern Engine.

``PatternResult`` (ein einzelnes erkanntes Muster) ist in ``patterns.base``
definiert – dort, damit kein Import-Zyklus zwischen ``patterns`` und
``engines`` entsteht – und wird hier re-exportiert. ``PatternReport`` bündelt
alle erkannten Muster eines Laufs samt Lauf-Metadaten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from patterns.base import PatternDirection, PatternResult, PatternType

__all__ = ["PatternResult", "PatternType", "PatternDirection", "PatternReport"]


@dataclass(slots=True)
class PatternReport:
    """Gesamtergebnis eines Pattern-Laufs für ein Symbol.

    Attributes:
        results: Alle erkannten Muster.
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen (z. B. übersprungene Muster).
        metadata: Zusatzinformationen (Symbol, Timeframe, Kerzenanzahl, …).
    """

    results: list[PatternResult] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_name(self, name: str) -> list[PatternResult]:
        """Gibt alle erkannten Muster eines bestimmten Namens zurück."""
        return [r for r in self.results if r.name == name]

    def by_direction(self, direction: PatternDirection) -> list[PatternResult]:
        """Gibt alle erkannten Muster einer bestimmten Richtung zurück."""
        return [r for r in self.results if r.direction is direction]

    @property
    def pattern_count(self) -> int:
        """Anzahl erkannter Muster."""
        return len(self.results)
