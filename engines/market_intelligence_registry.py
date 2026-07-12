"""Registry der verfügbaren Bewertungsmodelle.

Die Registry ist die **einzige** Stelle, an der Bewertungsmodelle bekannt gemacht
werden. Neue Modelle werden ausschließlich hier registriert; die
:class:`~engines.market_intelligence_engine.MarketIntelligenceEngine` kennt nur
die Registry, nicht die einzelnen Modellklassen, und muss für neue Modelle
**niemals** geändert werden (Open/Closed-Prinzip). Erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from market_intelligence.base import BaseOpportunityModel
from market_intelligence.opportunity import (
    AnalyticsOpportunityModel,
    BacktestOpportunityModel,
    PaperTradingOpportunityModel,
    RecommendationOpportunityModel,
    RiskOpportunityModel,
)


class MarketIntelligenceRegistry(Registry[BaseOpportunityModel]):
    """Verwaltet die verfügbaren Bewertungsmodelle nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Bewertungsmodell")


def build_default_registry() -> MarketIntelligenceRegistry:
    """Erzeugt eine Registry mit allen fünf Standard-Bewertungsmodellen."""
    registry = MarketIntelligenceRegistry()
    for model in (
        RecommendationOpportunityModel(),
        RiskOpportunityModel(),
        AnalyticsOpportunityModel(),
        BacktestOpportunityModel(),
        PaperTradingOpportunityModel(),
    ):
        registry.register(model)
    return registry
