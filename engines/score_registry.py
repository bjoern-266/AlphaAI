"""Registry der verfügbaren Score-Modelle.

Die Registry ist die **einzige** Stelle, an der Score-Modelle bekannt gemacht
werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`ScoreRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Modellklassen (Open/Closed-Prinzip).
"""

from __future__ import annotations

from scores.base import BaseScoreModel
from scores.confidence_score import ConfidenceScoreModel
from scores.consensus_score import ConsensusScoreModel
from scores.market_score import MarketScoreModel
from scores.quality_score import QualityScoreModel
from scores.weighted_score import WeightedScoreModel


class ScoreRegistry:
    """Verwaltet die verfügbaren Score-Modelle nach Name."""

    def __init__(self) -> None:
        self._by_name: dict[str, BaseScoreModel] = {}

    def register(self, model: BaseScoreModel) -> None:
        """Registriert ein Score-Modell.

        Raises:
            ValueError: Wenn bereits ein Modell mit demselben Namen existiert.
        """
        if model.name in self._by_name:
            raise ValueError(f"Score-Modell '{model.name}' ist bereits registriert.")
        self._by_name[model.name] = model

    def get(self, name: str) -> BaseScoreModel:
        """Gibt das Score-Modell mit dem Namen zurück.

        Raises:
            KeyError: Wenn kein Modell mit diesem Namen registriert ist.
        """
        if name not in self._by_name:
            raise KeyError(f"Unbekanntes Score-Modell '{name}'.")
        return self._by_name[name]

    def __contains__(self, name: str) -> bool:
        """Prüft, ob ein Modellname registriert ist."""
        return name in self._by_name

    def names(self) -> list[str]:
        """Gibt die registrierten Modellnamen sortiert zurück."""
        return sorted(self._by_name)

    def __len__(self) -> int:
        """Anzahl registrierter Modelle."""
        return len(self._by_name)


def build_default_registry() -> ScoreRegistry:
    """Erzeugt eine Registry mit allen Standard-Score-Modellen.

    Returns:
        Eine :class:`ScoreRegistry` mit den fünf Standard-Modellen.
    """
    registry = ScoreRegistry()
    for model in (
        WeightedScoreModel(),
        ConfidenceScoreModel(),
        QualityScoreModel(),
        ConsensusScoreModel(),
        MarketScoreModel(),
    ):
        registry.register(model)
    return registry
