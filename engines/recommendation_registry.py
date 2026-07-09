"""Registry der verfügbaren Recommendation-Modelle.

Die Registry ist die **einzige** Stelle, an der Recommendation-Modelle bekannt
gemacht werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`RecommendationRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Modellklassen (Open/Closed-Prinzip). Erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from recommendation.base import BaseRecommendationModel
from recommendation.confidence_model import ConfidenceModel
from recommendation.decision_model import DecisionModel
from recommendation.explanation_model import ExplanationModel
from recommendation.recommendation_model import RecommendationModel
from recommendation.summary_model import SummaryModel


class RecommendationRegistry(Registry[BaseRecommendationModel]):
    """Verwaltet die verfügbaren Recommendation-Modelle nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Recommendation-Modell")


def build_default_registry() -> RecommendationRegistry:
    """Erzeugt eine Registry mit allen Standard-Recommendation-Modellen.

    Returns:
        Eine :class:`RecommendationRegistry` mit den fünf Standard-Modellen.
    """
    registry = RecommendationRegistry()
    for model in (
        DecisionModel(),
        RecommendationModel(),
        ConfidenceModel(),
        SummaryModel(),
        ExplanationModel(),
    ):
        registry.register(model)
    return registry
