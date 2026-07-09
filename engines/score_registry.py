"""Registry der verfügbaren Score-Modelle.

Die Registry ist die **einzige** Stelle, an der Score-Modelle bekannt gemacht
werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`ScoreRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Modellklassen (Open/Closed-Prinzip).
"""

from __future__ import annotations

from core.registry import Registry
from scores.base import BaseScoreModel
from scores.confidence_score import ConfidenceScoreModel
from scores.consensus_score import ConsensusScoreModel
from scores.market_score import MarketScoreModel
from scores.quality_score import QualityScoreModel
from scores.weighted_score import WeightedScoreModel


class ScoreRegistry(Registry[BaseScoreModel]):
    """Verwaltet die verfügbaren Score-Modelle nach Name.

    Erbt Registrierung/Abfrage von der generischen :class:`core.registry.Registry`;
    das öffentliche Interface bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Score-Modell")


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
