"""Gemeinsame Schnittstelle und Hilfsmittel für Backtest-Modelle.

Alle Backtest-Modelle implementieren :class:`BaseBacktestModel` und geben ihr
Ergebnis als :class:`~models.backtest.BacktestModelOutput` zurück. Die reinen
Datentypen liegen in :mod:`models.backtest`; die Parameter-Fehlerklasse
:class:`BacktestParameterError` in :mod:`core.exceptions`. Beide werden hier zur
Bequemlichkeit re-exportiert.

Hier stehen außerdem kleine gemeinsame **Parameter-Hilfen**. Sie sind kein
eigenes Modell, damit kein Modell von einem anderen abhängt. Die eigentlichen
Kennzahl-Berechnungen liegen fachlich getrennt in den Hilfsmodulen des Pakets
(``performance_metrics``, ``equity_curve``, ``statistics``, ``benchmark``).

Die Modelle bewerten ausschließlich objektiv, wie sich **bestehende**
Empfehlungen entwickelt hätten – keine neue Handelsregel, keine Order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from core.exceptions import BacktestParameterError
from models.backtest import BacktestContext, BacktestModelOutput

__all__ = [
    "BacktestParameterError",
    "BacktestContext",
    "BacktestModelOutput",
    "BaseBacktestModel",
    "require_float",
    "require_int",
    "require_bool",
]


class BaseBacktestModel(ABC):
    """Basisklasse für alle Backtest-Modelle.

    Attributes:
        name: Eindeutiger Modellname (= Schlüssel in ``backtest_rules.toml``).
        value_range: Beschreibung des Wertebereichs (Dokumentation).
    """

    name: str = "base"
    value_range: str = "modellabhängig"

    @abstractmethod
    def compute(self, context: BacktestContext, params: Mapping[str, Any]) -> BacktestModelOutput:
        """Erzeugt den Kennzahl-Beitrag dieses Modells.

        Args:
            context: Trades, Kapitalkurve, Benchmark und Rahmenwerte des Laufs.
            params: Parameter des Modells (aus ``backtest_rules.toml``).

        Returns:
            Ein :class:`BacktestModelOutput` mit numerischen Kennzahlen.
        """
        raise NotImplementedError


def require_float(params: Mapping[str, Any], key: str, model: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (≥ 0)."""
    if key not in params:
        raise BacktestParameterError(f"'{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise BacktestParameterError(f"'{model}': Parameter '{key}' muss eine Zahl ≥ 0 sein.")
    return float(value)


def require_int(params: Mapping[str, Any], key: str, model: str) -> int:
    """Liest einen ganzzahligen Pflichtparameter (≥ 0)."""
    if key not in params:
        raise BacktestParameterError(f"'{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BacktestParameterError(f"'{model}': Parameter '{key}' muss eine ganze Zahl ≥ 0 sein.")
    return int(value)


def require_bool(params: Mapping[str, Any], key: str, model: str) -> bool:
    """Liest einen booleschen Pflichtparameter."""
    if key not in params:
        raise BacktestParameterError(f"'{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, bool):
        raise BacktestParameterError(f"'{model}': Parameter '{key}' muss true/false sein.")
    return value
