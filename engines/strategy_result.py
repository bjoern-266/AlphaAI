"""Ergebnistypen der Strategy Engine.

``StrategyResult`` (eine einzelne Hypothese) ist in ``strategies.base``
definiert – dort, damit kein Import-Zyklus zwischen ``strategies`` und
``engines`` entsteht – und wird hier re-exportiert. ``StrategyReport`` bündelt
alle Hypothesen eines Laufs samt Lauf-Metadaten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from strategies.base import StrategyDirection, StrategyResult

__all__ = ["StrategyResult", "StrategyDirection", "StrategyReport"]


@dataclass(slots=True)
class StrategyReport:
    """Gesamtergebnis eines Strategie-Laufs für ein Symbol.

    Attributes:
        results: Alle erzeugten Hypothesen.
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen (z. B. übersprungene Strategien).
        metadata: Zusatzinformationen (Symbol, Timeframe, …).
    """

    results: list[StrategyResult] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_name(self, name: str) -> list[StrategyResult]:
        """Gibt alle Hypothesen einer bestimmten Strategie zurück."""
        return [r for r in self.results if r.strategy_name == name]

    def by_direction(self, direction: StrategyDirection) -> list[StrategyResult]:
        """Gibt alle Hypothesen einer bestimmten Richtung zurück."""
        return [r for r in self.results if r.direction is direction]

    @property
    def bullish(self) -> list[StrategyResult]:
        """Alle bullischen Hypothesen."""
        return self.by_direction(StrategyDirection.BULLISH)

    @property
    def bearish(self) -> list[StrategyResult]:
        """Alle bärischen Hypothesen."""
        return self.by_direction(StrategyDirection.BEARISH)

    @property
    def hypothesis_count(self) -> int:
        """Anzahl erzeugter Hypothesen."""
        return len(self.results)
