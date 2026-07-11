"""Gemeinsame Schnittstelle und Hilfsmittel für Analysemodelle.

Alle Modelle implementieren :class:`BaseAnalyticsModel` und geben ihr Ergebnis
als :class:`~models.analytics.AnalyticsModelOutput` zurück. Die reinen Datentypen
liegen in :mod:`models.analytics`; die Parameter-Fehlerklasse
:class:`AnalyticsParameterError` in :mod:`core.exceptions`. Beide werden hier
re-exportiert.

Die Modelle erzeugen ausschließlich objektive Statistiken – keine
Handelsentscheidung, keine Bewertung, keine Veränderung bestehender Ergebnisse.
Sie arbeiten **unabhängig** voneinander (kein Modell importiert ein anderes).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from core.exceptions import AnalyticsParameterError
from models.analytics import AnalyticsContext, AnalyticsModelOutput

__all__ = [
    "AnalyticsParameterError",
    "AnalyticsContext",
    "AnalyticsModelOutput",
    "BaseAnalyticsModel",
    "require_float",
]


class BaseAnalyticsModel(ABC):
    """Basisklasse für alle Analysemodelle.

    Attributes:
        name: Eindeutiger Modellname (= Schlüssel in ``analytics_rules.toml``).
        value_range: Beschreibung des Wertebereichs (Dokumentation).
    """

    name: str = "base"
    value_range: str = "Statistiken"

    @abstractmethod
    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Erzeugt den Statistik-Beitrag dieses Modells.

        Args:
            context: Normalisierte Trades, Journal, Konfiguration und Rahmenwerte.
            params: Parameter des Modells (aus ``analytics_rules.toml``).

        Returns:
            Ein :class:`AnalyticsModelOutput`.
        """
        raise NotImplementedError


def require_float(params: Mapping[str, Any], key: str, model: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (≥ 0)."""
    if key not in params:
        raise AnalyticsParameterError(f"'{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise AnalyticsParameterError(f"'{model}': Parameter '{key}' muss eine Zahl ≥ 0 sein.")
    return float(value)
