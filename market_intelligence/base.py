"""Gemeinsame Schnittstelle und Hilfsmittel für Bewertungsmodelle.

Alle Modelle implementieren :class:`BaseOpportunityModel` und geben ihren
Score-Beitrag als :class:`~models.opportunity.OpportunityModelOutput` zurück. Ein
Modell **berechnet keine neue Handelsregel**: es leitet seinen Beitrag
ausschließlich aus einer **bereits vorhandenen** Kennzahl ab (Recommendation,
Risk, Analytics, Backtesting, Paper Trading). Die Modelle arbeiten **unabhängig**
voneinander (kein Modell importiert ein anderes).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any

from core.exceptions import MarketIntelligenceParameterError
from models.opportunity import MarketIntelligenceContext, OpportunityModelOutput

__all__ = [
    "MarketIntelligenceParameterError",
    "MarketIntelligenceContext",
    "OpportunityModelOutput",
    "BaseOpportunityModel",
    "require_weight",
    "clamp_score",
]


class BaseOpportunityModel(ABC):
    """Basisklasse für alle Bewertungsmodelle.

    Attributes:
        name: Eindeutiger Modellname (= Schlüssel in
            ``market_intelligence_rules.toml``).
        source: Beschreibung der ausgewerteten Quelle (Dokumentation).
    """

    name: str = "base"
    source: str = "bestehende Kennzahl"

    @abstractmethod
    def compute(
        self, context: MarketIntelligenceContext, params: Mapping[str, Any]
    ) -> OpportunityModelOutput:
        """Erzeugt den Score-Beitrag dieses Modells (aus vorhandenen Kennzahlen).

        Args:
            context: Die zu bewertende Aktie mit ihren vorhandenen Reports.
            params: Parameter des Modells (aus ``market_intelligence_rules.toml``).

        Returns:
            Ein :class:`OpportunityModelOutput`.
        """
        raise NotImplementedError


def require_weight(params: Mapping[str, Any], model: str) -> float:
    """Liest das Pflicht-Gewicht eines Modells (0..1).

    Raises:
        MarketIntelligenceParameterError: Wenn das Gewicht fehlt oder ungültig ist.
    """
    if "weight" not in params:
        raise MarketIntelligenceParameterError(f"'{model}': Parameter 'weight' fehlt.")
    value = params["weight"]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0.0 <= value <= 1.0:
        raise MarketIntelligenceParameterError(
            f"'{model}': Parameter 'weight' muss zwischen 0 und 1 liegen."
        )
    return float(value)


def clamp_score(value: float, config: Mapping[str, Any]) -> float:
    """Begrenzt einen Score auf den konfigurierten Wertebereich (Standard 0..100)."""
    low = float(config.get("score_min", 0.0))
    high = float(config.get("score_max", 100.0))
    return max(low, min(high, float(value)))
