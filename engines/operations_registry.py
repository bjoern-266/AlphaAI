"""Registry der bekannten Job-Arten.

Die Registry ist die **einzige** Stelle, an der Job-Arten bekannt gemacht werden.
Neue Job-Arten werden ausschließlich hier registriert; die
:class:`~engines.operations_engine.OperationsEngine` kennt nur die Registry und
bleibt für neue Job-Arten **unverändert** (Open/Closed). Erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from core.registry import Registry
from models.operations import JobDefinition


class OperationsRegistry(Registry[JobDefinition]):
    """Verwaltet die bekannten Job-Arten nach Schlüssel.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Job-Art")


# Die Standard-Job-Arten (weitere werden hier ergänzt; die Engine bleibt gleich).
_DEFAULT_JOBS: tuple[JobDefinition, ...] = (
    JobDefinition("discovery", "Market Discovery", "Durchsucht den Markt", exclusive=True),
    JobDefinition("scanner", "Scanner", "Scannt das Universum"),
    JobDefinition("analytics", "Analytics", "Wertet Ergebnisse aus"),
    JobDefinition("market_intelligence", "Market Intelligence", "Priorisiert Chancen"),
    JobDefinition("dashboard_refresh", "Dashboard Refresh", "Lädt die Reports neu"),
    JobDefinition(
        "paper_trading_update", "Paper Trading Update", "Aktualisiert das Paper-Portfolio"
    ),
    JobDefinition("backtest_refresh", "Backtest Refresh", "Aktualisiert Backtests (optional)"),
)


def build_default_registry() -> OperationsRegistry:
    """Erzeugt eine Registry mit allen Standard-Job-Arten."""
    registry = OperationsRegistry()
    for definition in _DEFAULT_JOBS:
        registry.register(definition)
    return registry
