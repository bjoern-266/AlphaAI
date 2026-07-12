"""Registry der bekannten Report-Arten des Backend-Dienstes.

Die Registry ist die **einzige** Stelle, an der die vom Backend ausgelieferten
Report-Arten bekannt gemacht werden. Neue Arten werden ausschließlich hier
ergänzt; die :class:`~engines.application_engine.ApplicationEngine` und die API
bleiben dafür **unverändert** (Open/Closed). Sie erbt von der generischen
:class:`core.registry.Registry`.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.registry import Registry
from models.application import ReportKind


@dataclass(frozen=True, slots=True)
class ReportKindDescriptor:
    """Beschreibung einer vom Backend ausgelieferten Report-Art.

    Attributes:
        name: Stabiler Schlüssel der Art (= Wert aus :class:`ReportKind`).
        title: Anzeigename der Art.
        description: Kurzbeschreibung.
        composite: Ob die Art aus mehreren Reports zusammengesetzt ist (Dashboard).
    """

    name: str
    title: str = ""
    description: str = ""
    composite: bool = False


class ApplicationRegistry(Registry[ReportKindDescriptor]):
    """Verwaltet die bekannten Report-Arten nach Schlüssel.

    Das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) stammt aus der generischen Basis und bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Report-Art")


# Die Standard-Report-Arten (weitere werden hier ergänzt; die Engine bleibt gleich).
_DEFAULT_KINDS: tuple[ReportKindDescriptor, ...] = (
    ReportKindDescriptor(ReportKind.OPERATIONS.value, "Operations", "Live Operations Report"),
    ReportKindDescriptor(ReportKind.DISCOVERY.value, "Discovery", "Market Discovery Report"),
    ReportKindDescriptor(
        ReportKind.OPPORTUNITIES.value, "Opportunities", "Market Intelligence Chancen"
    ),
    ReportKindDescriptor(ReportKind.RECOMMENDATIONS.value, "Recommendations", "Empfehlungs-Report"),
    ReportKindDescriptor(ReportKind.ANALYTICS.value, "Analytics", "Analytics-Report"),
    ReportKindDescriptor(ReportKind.BACKTESTING.value, "Backtesting", "Backtesting-Report"),
    ReportKindDescriptor(ReportKind.PAPER_TRADING.value, "Paper Trading", "Paper-Trading-Report"),
    ReportKindDescriptor(
        ReportKind.DASHBOARD.value,
        "Dashboard",
        "Zusammengesetzter Schnappschuss aller Reports",
        composite=True,
    ),
)


def build_default_registry() -> ApplicationRegistry:
    """Erzeugt eine Registry mit allen Standard-Report-Arten."""
    registry = ApplicationRegistry()
    for descriptor in _DEFAULT_KINDS:
        registry.register(descriptor)
    return registry


__all__ = ["ApplicationRegistry", "ReportKindDescriptor", "build_default_registry"]
