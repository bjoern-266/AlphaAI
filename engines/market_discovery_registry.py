"""Registry der unterstützten Märkte.

Die Registry ist die **einzige** Stelle, an der Märkte bekannt gemacht werden.
Weitere Märkte lassen sich problemlos ergänzen – ausschließlich hier registriert;
die :class:`~engines.market_discovery_engine.MarketDiscoveryEngine` kennt nur die
Registry, nicht die einzelnen Markt-Definitionen, und bleibt für neue Märkte
**unverändert** (Open/Closed). Erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from models.market_discovery import MarketDefinition


class MarketDiscoveryRegistry(Registry[MarketDefinition]):
    """Verwaltet die unterstützten Märkte nach Schlüssel.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Markt")


# Die unterstützten Standard-Märkte. Weitere Märkte werden hier ergänzt (die
# Engine bleibt unverändert).
_DEFAULT_MARKETS: tuple[MarketDefinition, ...] = (
    MarketDefinition("nyse", "NYSE", country="US", exchange="NYSE"),
    MarketDefinition("nasdaq", "NASDAQ", country="US", exchange="NASDAQ"),
    MarketDefinition("sp500", "S&P 500", country="US", exchange=""),
    MarketDefinition("nasdaq100", "NASDAQ 100", country="US", exchange="NASDAQ"),
    MarketDefinition("russell2000", "Russell 2000", country="US", exchange=""),
    MarketDefinition("dax", "DAX", country="DE", exchange="XETRA"),
    MarketDefinition("mdax", "MDAX", country="DE", exchange="XETRA"),
    MarketDefinition("sdax", "SDAX", country="DE", exchange="XETRA"),
    MarketDefinition("tecdax", "TecDAX", country="DE", exchange="XETRA"),
    MarketDefinition("eurostoxx50", "Euro Stoxx 50", country="EU", exchange=""),
)


def build_default_registry() -> MarketDiscoveryRegistry:
    """Erzeugt eine Registry mit allen unterstützten Standard-Märkten."""
    registry = MarketDiscoveryRegistry()
    for definition in _DEFAULT_MARKETS:
        registry.register(definition)
    return registry
