"""Gemeinsame Schnittstelle, Ergebnistypen und Hilfsmittel für Muster.

Alle Muster implementieren :class:`BasePattern` und geben ihr Ergebnis als
:class:`PatternDetection` (Liste von :class:`PatternResult` plus Warnungen)
zurück. Die Ergebnistypen liegen bewusst hier (nicht in ``engines``), damit
kein Import-Zyklus zwischen ``patterns`` und ``engines`` entsteht.

Gemeinsame Hilfsmittel (Swing-Erkennung, Struktur-Break-Erkennung,
Parameterprüfung, Skalierung) sind kein eigenes Muster – sie stehen hier, damit
kein Muster von einem anderen Muster abhängt.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd


class PatternParameterError(ValueError):
    """Wird ausgelöst, wenn ein Pflichtparameter fehlt oder ungültig ist."""


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


@dataclass(slots=True)
class PatternResult:
    """Ein einzelnes erkanntes Muster.

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


@dataclass(slots=True)
class PatternDetection:
    """Ergebnis eines einzelnen Muster-Detektors.

    Attributes:
        patterns: Erkannte Muster (kann leer sein).
        warnings: Während der Erkennung gesammelte Warnungen.
    """

    patterns: list[PatternResult] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class BasePattern(ABC):
    """Basisklasse für alle Muster-Detektoren.

    Attributes:
        name: Eindeutiger Mustername (z. B. ``"fvg"``).
        pattern_type: Kategorie des Musters.
        implemented: Ob der Detektor tatsächlich Muster erkennt. Vorbereitete
            Muster setzen dies auf ``False``.
    """

    name: str = "base"
    pattern_type: PatternType = PatternType.MARKET_STRUCTURE
    implemented: bool = True

    @abstractmethod
    def detect(self, data: pd.DataFrame, params: Mapping[str, Any]) -> PatternDetection:
        """Erkennt Muster auf den übergebenen OHLCV-Daten.

        Args:
            data: OHLCV-DataFrame im kanonischen Schema.
            params: Parameter des Musters (aus der Konfiguration).

        Returns:
            Eine :class:`PatternDetection`.
        """
        raise NotImplementedError

    @abstractmethod
    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Gibt die minimal benötigte Anzahl an Kerzen zurück."""
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Parameter-Hilfen                                                             #
# --------------------------------------------------------------------------- #


def require_int(params: Mapping[str, Any], key: str, pattern: str) -> int:
    """Liest einen ganzzahligen Pflichtparameter (> 0)."""
    if key not in params:
        raise PatternParameterError(f"Muster '{pattern}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise PatternParameterError(
            f"Muster '{pattern}': Parameter '{key}' muss eine positive Ganzzahl sein."
        )
    return value


def require_float(params: Mapping[str, Any], key: str, pattern: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (> 0)."""
    if key not in params:
        raise PatternParameterError(f"Muster '{pattern}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise PatternParameterError(
            f"Muster '{pattern}': Parameter '{key}' muss eine positive Zahl sein."
        )
    return float(value)


def scaled_strength(ratio: float, full_scale_ratio: float) -> float:
    """Skaliert ein Verhältnis linear auf 0..100.

    Ein ``ratio`` gleich ``full_scale_ratio`` ergibt 100. Der Wert wird auf
    0..100 begrenzt. Dies ist eine beschreibende Kennzahl, kein Signal.
    """
    if full_scale_ratio <= 0:
        return 0.0
    return float(min(100.0, max(0.0, ratio / full_scale_ratio * 100.0)))


# --------------------------------------------------------------------------- #
# Swing-Erkennung (gemeinsames Hilfsmittel, kein Muster)                       #
# --------------------------------------------------------------------------- #


def swing_highs(data: pd.DataFrame, left: int, right: int) -> list[int]:
    """Ermittelt die Positionsindizes lokaler Hochs (Swing Highs).

    Ein Index ``i`` ist ein Swing High, wenn ``high[i]`` strikt größer ist als
    alle ``left`` Kerzen davor und alle ``right`` Kerzen danach.
    """
    highs = data["high"].to_numpy()
    n = len(highs)
    result: list[int] = []
    for i in range(left, n - right):
        pivot = highs[i]
        if all(pivot > highs[j] for j in range(i - left, i)) and all(
            pivot > highs[j] for j in range(i + 1, i + 1 + right)
        ):
            result.append(i)
    return result


def swing_lows(data: pd.DataFrame, left: int, right: int) -> list[int]:
    """Ermittelt die Positionsindizes lokaler Tiefs (Swing Lows)."""
    lows = data["low"].to_numpy()
    n = len(lows)
    result: list[int] = []
    for i in range(left, n - right):
        pivot = lows[i]
        if all(pivot < lows[j] for j in range(i - left, i)) and all(
            pivot < lows[j] for j in range(i + 1, i + 1 + right)
        ):
            result.append(i)
    return result


# --------------------------------------------------------------------------- #
# Struktur-Break-Erkennung (gemeinsames Hilfsmittel, kein Muster)             #
# --------------------------------------------------------------------------- #


@dataclass(slots=True)
class StructureBreak:
    """Ein Bruch der Marktstruktur.

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


def detect_structure_breaks(data: pd.DataFrame, swing_lookback: int) -> list[StructureBreak]:
    """Erkennt Struktur-Brüche (BOS/CHoCH) anhand von Swing-Punkten.

    Verfahren (bewusst einfach und deterministisch):

    1. Swing Highs/Lows werden mit ``swing_lookback`` Kerzen je Seite bestimmt.
       Ein Swing ist erst ``swing_lookback`` Kerzen später bestätigt.
    2. Es werden das jüngste bestätigte Swing High und Swing Low mitgeführt.
    3. Schließt eine Kerze über dem letzten Swing High, ist das ein bullischer
       Bruch; schließt sie unter dem letzten Swing Low, ein bärischer.
    4. Ein Bruch in Trendrichtung ist ein BOS, gegen den Trend ein CHoCH. Der
       erste Bruch (Trend noch unbestimmt) gilt als BOS.

    Args:
        data: OHLCV-DataFrame.
        swing_lookback: Kerzen je Seite zur Swing-Bestätigung.

    Returns:
        Chronologische Liste der erkannten Struktur-Brüche.
    """
    high_pivots = sorted(
        (idx + swing_lookback, float(data["high"].iloc[idx]))
        for idx in swing_highs(data, swing_lookback, swing_lookback)
    )
    low_pivots = sorted(
        (idx + swing_lookback, float(data["low"].iloc[idx]))
        for idx in swing_lows(data, swing_lookback, swing_lookback)
    )

    close = data["close"].to_numpy()
    index = data.index
    events: list[StructureBreak] = []

    ref_high: float | None = None
    ref_low: float | None = None
    trend = 0
    hi = 0
    li = 0
    n = len(data)
    for bar in range(n):
        while hi < len(high_pivots) and high_pivots[hi][0] == bar:
            ref_high = high_pivots[hi][1]
            hi += 1
        while li < len(low_pivots) and low_pivots[li][0] == bar:
            ref_low = low_pivots[li][1]
            li += 1

        price = close[bar]
        if ref_high is not None and price > ref_high:
            kind = "bos" if trend >= 0 else "choch"
            events.append(StructureBreak(bar, index[bar], ref_high, PatternDirection.BULLISH, kind))
            trend = 1
            ref_high = None
        elif ref_low is not None and price < ref_low:
            kind = "bos" if trend <= 0 else "choch"
            events.append(StructureBreak(bar, index[bar], ref_low, PatternDirection.BEARISH, kind))
            trend = -1
            ref_low = None
    return events
