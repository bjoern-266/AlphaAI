"""Domänenmodell: Muster-Ergebnisse.

Enthält die unveränderlichen Datentypen der Pattern Engine: die Enums
:class:`PatternType`/:class:`PatternDirection`, das einzelne
:class:`PatternResult`, das Detektor-Ergebnis :class:`PatternDetection`, den
Struktur-Bruch :class:`StructureBreak` und den Lauf-Report
:class:`PatternReport`. Teil der Entities-Schicht (``models/``) – importiert
nichts aus höheren Schichten.

Die Erkennungs-*Logik* (Swing-/Struktur-Erkennung, Parameterprüfung) bleibt in
``patterns.base``. Zur Rückwärtskompatibilität werden diese Typen unter
``patterns.base`` bzw. ``engines.pattern_result`` re-exportiert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PatternType(Enum):
    """Kategorie eines Musters."""

    FAIR_VALUE_GAP = "fair_value_gap"
    STRUCTURE_BREAK = "structure_break"
    EQUAL_LEVEL = "equal_level"
    LIQUIDITY = "liquidity"
    MARKET_STRUCTURE = "market_structure"
    TREND = "trend"
    ORDER_BLOCK = "order_block"
    BREAKER_BLOCK = "breaker_block"
    MITIGATION_BLOCK = "mitigation_block"


class PatternDirection(Enum):
    """Richtung/Bias eines Musters."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class PatternResult:
    """Ein einzelnes erkanntes Muster (unveränderlich).

    Attributes:
        name: Name des Musters (z. B. ``"fvg"``).
        pattern_type: Kategorie des Musters.
        direction: Richtung/Bias (bullish/bearish/neutral).
        strength: Ausprägung 0..100 (beschreibend, keine Bewertung/Signal).
        confidence: Vertrauen 0..1 in die Erkennung.
        timestamp: Zeitpunkt des Musters (Index der auslösenden Kerze).
        price_level: Charakteristisches Preisniveau des Musters.
        metadata: Zusätzliche Detailinformationen.
    """

    name: str
    pattern_type: PatternType
    direction: PatternDirection
    strength: float
    confidence: float
    timestamp: datetime | None = None
    price_level: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PatternDetection:
    """Ergebnis eines einzelnen Muster-Detektors (unveränderlich).

    Attributes:
        patterns: Erkannte Muster (kann leer sein).
        warnings: Während der Erkennung gesammelte Warnungen.
    """

    patterns: list[PatternResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class StructureBreak:
    """Ein Bruch der Marktstruktur (unveränderlich).

    Attributes:
        index: Positionsindex der auslösenden Kerze.
        timestamp: Zeitstempel der auslösenden Kerze.
        level: Durchbrochenes Preisniveau (vorheriger Swing).
        direction: Richtung des Bruchs.
        kind: ``"bos"`` (Trendfortsetzung) oder ``"choch"`` (Trendwechsel).
    """

    index: int
    timestamp: datetime
    level: float
    direction: PatternDirection
    kind: str


@dataclass(frozen=True, slots=True)
class PatternReport:
    """Gesamtergebnis eines Pattern-Laufs für ein Symbol (unveränderlich).

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
