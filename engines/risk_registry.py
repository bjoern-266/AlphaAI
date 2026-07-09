"""Registry der verfügbaren Risk-Modelle.

Die Registry ist die **einzige** Stelle, an der Risk-Modelle bekannt gemacht
werden. Neue Modelle werden ausschließlich hier registriert
(:meth:`RiskRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Modellklassen (Open/Closed-Prinzip). Erbt Registrierung/Abfrage von
der generischen :class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from risk.base import BaseRiskModel
from risk.correlation_risk import CorrelationRiskModel
from risk.execution_risk import ExecutionRiskModel
from risk.gap_risk import GapRiskModel
from risk.liquidity_risk import LiquidityRiskModel
from risk.market_risk import MarketRiskModel
from risk.portfolio_risk import PortfolioRiskModel
from risk.position_sizing import PositionSizingModel
from risk.volatility_risk import VolatilityRiskModel


class RiskRegistry(Registry[BaseRiskModel]):
    """Verwaltet die verfügbaren Risk-Modelle nach Name.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Risk-Modell")


def build_default_registry() -> RiskRegistry:
    """Erzeugt eine Registry mit allen Standard-Risk-Modellen.

    Returns:
        Eine :class:`RiskRegistry` mit den acht Standard-Modellen.
    """
    registry = RiskRegistry()
    for model in (
        PositionSizingModel(),
        VolatilityRiskModel(),
        LiquidityRiskModel(),
        GapRiskModel(),
        MarketRiskModel(),
        CorrelationRiskModel(),
        PortfolioRiskModel(),
        ExecutionRiskModel(),
    ):
        registry.register(model)
    return registry
