"""Gemeinsame Schnittstelle und Hilfsmittel für Strategien.

Alle Strategien implementieren :class:`BaseStrategy` und geben ihr Ergebnis als
:class:`~models.strategy.StrategyEvaluation` zurück.

Die reinen Datentypen (``StrategyDirection``, ``StrategyContext``,
``StrategyResult``, ``StrategyEvaluation``, ``StrategyReport``) liegen seit
Sprint 7.5 in :mod:`models.strategy`; :class:`StrategyParameterError` in
:mod:`core.exceptions`. Sie werden hier zur Rückwärtskompatibilität
re-exportiert. Dieses Modul enthält ausschließlich Schnittstelle und Logik –
und importiert **nichts** aus ``engines`` (die frühere ``TYPE_CHECKING``-
Kopplung ist damit aufgelöst).

Eine Strategie erzeugt ausschließlich eine **Hypothese** (Richtung, Vertrauen,
beschreibende Stärke, Begründungen). Sie trifft keine Handelsentscheidung und
vergibt keinen Gesamtscore.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from core.exceptions import StrategyParameterError
from models.strategy import (
    StrategyContext,
    StrategyDirection,
    StrategyEvaluation,
    StrategyResult,
)

__all__ = [
    "StrategyParameterError",
    "StrategyDirection",
    "StrategyContext",
    "StrategyResult",
    "StrategyEvaluation",
    "BaseStrategy",
    "require_float",
    "require_bool",
    "build_hypothesis_id",
    "direction_from_value",
]


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
