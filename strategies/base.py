"""Gemeinsame Schnittstelle, Ergebnistypen und Hilfsmittel für Strategien.

Alle Strategien implementieren :class:`BaseStrategy` und geben ihr Ergebnis als
:class:`StrategyEvaluation` zurück. Die Ergebnistypen liegen bewusst hier
(nicht in ``engines``), damit kein Import-Zyklus zwischen ``strategies`` und
``engines`` entsteht.

Eine Strategie erzeugt ausschließlich eine **Hypothese** (Richtung, Vertrauen,
beschreibende Stärke, Begründungen). Sie trifft keine Handelsentscheidung und
vergibt keinen Gesamtscore.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # nur für Typannotationen – kein Laufzeit-Import aus engines
    import pandas as pd

    from engines.indicator_result import IndicatorResult
    from engines.pattern_result import PatternReport


class StrategyParameterError(ValueError):
    """Wird ausgelöst, wenn ein Pflichtparameter fehlt oder ungültig ist."""


class StrategyDirection(Enum):
    """Richtung einer Handelshypothese."""

    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


@dataclass(slots=True)
class StrategyContext:
    """Eingabe für eine Strategie.

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


@dataclass(slots=True)
class StrategyResult:
    """Eine objektive Handelshypothese.

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


@dataclass(slots=True)
class StrategyEvaluation:
    """Ergebnis der Auswertung einer einzelnen Strategie.

    Attributes:
        result: Die erzeugte Hypothese oder ``None`` (kein Setup).
        warnings: Warnungen der Auswertung.
    """

    result: StrategyResult | None = None
    warnings: list[str] = field(default_factory=list)


class BaseStrategy(ABC):
    """Basisklasse für alle Strategien.

    Attributes:
        name: Eindeutiger Strategiename.
        description: Kurzbeschreibung der Strategie.
        version: Versionskennung der Strategie.
        pattern_requirements: Benötigte Muster (müssen vorhanden sein).
        indicator_requirements: Benötigte Indikatoren (müssen vorhanden sein).
    """

    name: str = "base"
    description: str = ""
    version: str = "1.0"
    pattern_requirements: tuple[str, ...] = ()
    indicator_requirements: tuple[str, ...] = ()

    @abstractmethod
    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        """Wertet die Strategie aus und erzeugt ggf. eine Hypothese.

        Args:
            context: Indikatoren, Muster und optionale Rohdaten.
            params: Parameter der Strategie (aus der Konfiguration).

        Returns:
            Eine :class:`StrategyEvaluation`.
        """
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Parameter-Hilfen                                                             #
# --------------------------------------------------------------------------- #


def require_float(params: Mapping[str, Any], key: str, strategy: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter."""
    if key not in params:
        raise StrategyParameterError(f"Strategie '{strategy}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StrategyParameterError(
            f"Strategie '{strategy}': Parameter '{key}' muss eine Zahl sein."
        )
    return float(value)


def require_bool(params: Mapping[str, Any], key: str, strategy: str) -> bool:
    """Liest einen booleschen Pflichtparameter."""
    if key not in params:
        raise StrategyParameterError(f"Strategie '{strategy}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, bool):
        raise StrategyParameterError(
            f"Strategie '{strategy}': Parameter '{key}' muss ein Wahrheitswert sein."
        )
    return value


def build_hypothesis_id(
    name: str, direction: StrategyDirection, symbol: str, timestamp: datetime | None
) -> str:
    """Erzeugt einen stabilen, lesbaren Bezeichner für eine Hypothese."""
    ts = timestamp.isoformat() if timestamp is not None else "na"
    return f"{name}:{direction.value}:{symbol or 'na'}:{ts}"


def direction_from_value(value: str) -> StrategyDirection:
    """Bildet einen Richtungs-String (z. B. eines Musters) auf die Enum ab."""
    return {
        "bullish": StrategyDirection.BULLISH,
        "bearish": StrategyDirection.BEARISH,
    }.get(value, StrategyDirection.NEUTRAL)
