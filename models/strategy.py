"""Domänenmodell: Strategie-Ergebnisse.

Enthält die unveränderlichen Datentypen der Strategy Engine: die Enum
:class:`StrategyDirection`, den Eingabe-Kontext :class:`StrategyContext`, die
einzelne Hypothese :class:`StrategyResult`, das Auswertungsergebnis
:class:`StrategyEvaluation` und den Lauf-Report :class:`StrategyReport`.

Teil der Entities-Schicht (``models/``). Die Abhängigkeiten zeigen ausschließlich
auf andere Modelle (:mod:`models.indicator`, :mod:`models.pattern`) – **kein**
Import aus ``engines`` mehr (löst die bisherige ``TYPE_CHECKING``-Kopplung auf).
Die Auswertungs-*Logik* und Hilfsfunktionen bleiben in ``strategies.base``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd

from models.indicator import IndicatorResult
from models.pattern import PatternReport


class StrategyDirection(Enum):
    """Richtung einer Handelshypothese."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class StrategyContext:
    """Eingabe für eine Strategie (unveränderlich).

    Attributes:
        indicators: Ergebnis der Indicator Engine.
        patterns: Ergebnis der Pattern Engine.
        data: Optionale OHLCV-Rohdaten (für Preisvergleiche).
        symbol: Symbolname.
        timeframe: Zeitebenen-Label.
    """

    indicators: IndicatorResult
    patterns: PatternReport
    data: pd.DataFrame | None = None
    symbol: str = ""
    timeframe: str = "base"

    @property
    def last_close(self) -> float | None:
        """Letzter Schlusskurs aus den Rohdaten oder ``None``."""
        if self.data is None or self.data.empty or "close" not in self.data.columns:
            return None
        return float(self.data["close"].iloc[-1])

    @property
    def last_timestamp(self) -> datetime | None:
        """Letzter Zeitstempel aus den Rohdaten oder ``None``."""
        if self.data is None or self.data.empty:
            return None
        return self.data.index[-1]


@dataclass(frozen=True, slots=True)
class StrategyResult:
    """Eine objektive Handelshypothese (unveränderlich).

    Attributes:
        strategy_name: Name der erzeugenden Strategie.
        hypothesis_id: Stabiler Bezeichner der Hypothese.
        direction: Richtung (bullish/bearish/neutral).
        confidence: Vertrauen 0..1 in die Hypothese.
        strength: Beschreibende Stärke 0..100 (kein Score, keine Bewertung).
        matched_indicators: Verwendete Indikatoren.
        matched_patterns: Verwendete Muster.
        reasons: Menschenlesbare Begründungen der Hypothese.
        warnings: Während der Auswertung gesammelte Warnungen.
        metadata: Zusatzinformationen (u. a. der Hypothesentext).
        timestamp: Zeitpunkt der Hypothese.
    """

    strategy_name: str
    hypothesis_id: str
    direction: StrategyDirection
    confidence: float
    strength: float
    matched_indicators: list[str] = field(default_factory=list)
    matched_patterns: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class StrategyEvaluation:
    """Ergebnis der Auswertung einer einzelnen Strategie (unveränderlich).

    Attributes:
        result: Die erzeugte Hypothese oder ``None`` (kein Setup).
        warnings: Warnungen der Auswertung.
    """

    result: StrategyResult | None = None
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class StrategyReport:
    """Gesamtergebnis eines Strategie-Laufs für ein Symbol (unveränderlich).

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
