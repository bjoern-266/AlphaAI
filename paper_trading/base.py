"""Gemeinsame Schnittstelle und Hilfsmittel für Paper-Trading-Modelle.

Alle Modelle implementieren :class:`BasePaperTradingModel` und geben ihr Ergebnis
als :class:`~models.paper_trading.PaperTradingModelOutput` zurück. Die reinen
Datentypen liegen in :mod:`models.paper_trading`; die Parameter-Fehlerklasse
:class:`PaperTradingParameterError` in :mod:`core.exceptions`. Beide werden hier
re-exportiert.

Die Modelle bewerten ausschließlich objektiv das simulierte Portfolio – keine
neue Handelsregel, keine echte Order.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from core.exceptions import PaperTradingParameterError
from models.paper_trading import PaperTradingContext, PaperTradingModelOutput

__all__ = [
    "PaperTradingParameterError",
    "PaperTradingContext",
    "PaperTradingModelOutput",
    "BasePaperTradingModel",
    "require_float",
]


class BasePaperTradingModel(ABC):
    """Basisklasse für alle Paper-Trading-Modelle.

    Attributes:
        name: Eindeutiger Modellname (= Schlüssel in
            ``paper_trading_rules.toml``).
        value_range: Beschreibung des Wertebereichs (Dokumentation).
    """

    name: str = "base"
    value_range: str = "modellabhängig"

    @abstractmethod
    def compute(
        self, context: PaperTradingContext, params: Mapping[str, Any]
    ) -> PaperTradingModelOutput:
        """Erzeugt den Kennzahl-Beitrag dieses Modells.

        Args:
            context: Positionen, Trades, Kapitalkurve und Rahmenwerte des Laufs.
            params: Parameter des Modells (aus ``paper_trading_rules.toml``).

        Returns:
            Ein :class:`PaperTradingModelOutput`.
        """
        raise NotImplementedError


def require_float(params: Mapping[str, Any], key: str, model: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (≥ 0)."""
    if key not in params:
        raise PaperTradingParameterError(f"'{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise PaperTradingParameterError(f"'{model}': Parameter '{key}' muss eine Zahl ≥ 0 sein.")
    return float(value)
