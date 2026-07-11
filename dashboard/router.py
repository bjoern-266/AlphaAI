"""Router des Command Center – ordnet jeder Seite ihre Widgets zu.

Neue Seiten werden **ausschließlich** hier (über den Router) ergänzt; die
:class:`~dashboard.engine.DashboardEngine` bleibt unverändert. Der Router enthält
**keine** Fachlogik – er beschreibt nur, welche Widgets in welcher Region einer
Seite angezeigt werden, sowie Navigationseinträge und Tastenkürzel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dashboard.state import Page

# Region-Reihenfolge des dreispaltigen Layouts.
REGIONS = ("left", "center", "right")


@dataclass(frozen=True, slots=True)
class PageLayout:
    """Beschreibung einer Seite (unveränderlich).

    Attributes:
        page: Die Seite.
        title: Anzeigetitel.
        icon: Semantischer Icon-Name (aus dem Theme).
        regions: Zuordnung Region → geordnete Widget-IDs.
    """

    page: Page
    title: str
    icon: str
    regions: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def widget_ids(self) -> tuple[str, ...]:
        """Alle Widget-IDs der Seite in Regionen-Reihenfolge."""
        ordered: list[str] = []
        for region in REGIONS:
            ordered.extend(self.regions.get(region, ()))
        return tuple(ordered)


@dataclass(frozen=True, slots=True)
class NavItem:
    """Ein Navigationseintrag der Sidebar (unveränderlich)."""

    page: Page
    title: str
    icon: str


class Router:
    """Verwaltet die Seiten-Layouts des Dashboards.

    Neue Seiten werden über :meth:`register` hinzugefügt; die Engine bleibt
    unverändert.
    """

    def __init__(self) -> None:
        self._layouts: dict[Page, PageLayout] = {}

    def register(self, layout: PageLayout) -> None:
        """Registriert (oder ersetzt) das Layout einer Seite."""
        self._layouts[layout.page] = layout

    def has(self, page: Page) -> bool:
        """Ob für eine Seite ein Layout registriert ist."""
        return page in self._layouts

    def resolve(self, page: Page) -> PageLayout:
        """Gibt das Layout einer Seite zurück (Fallback: leeres Layout)."""
        return self._layouts.get(page, PageLayout(page, page.value.title(), "", {}))

    def pages(self) -> tuple[Page, ...]:
        """Alle registrierten Seiten in Registrierungs-Reihenfolge."""
        return tuple(self._layouts)

    def nav_items(self, icons: dict[str, str] | None = None) -> tuple[NavItem, ...]:
        """Erzeugt die Navigationseinträge (Sidebar) aus den registrierten Seiten."""
        icons = icons or {}
        return tuple(
            NavItem(layout.page, layout.title, icons.get(layout.page.value, layout.icon))
            for layout in self._layouts.values()
        )


# Titel je Seite (Anzeige).
_TITLES: dict[Page, str] = {
    Page.OVERVIEW: "Overview",
    Page.LIVE_ANALYSIS: "Live Analysis",
    Page.PAPER_PORTFOLIO: "Paper Portfolio",
    Page.BACKTESTING: "Backtesting",
    Page.ANALYTICS: "Analytics",
    Page.PERFORMANCE: "Performance",
    Page.TRADE_JOURNAL: "Trade Journal",
    Page.RECOMMENDATIONS: "Recommendations",
    Page.SETTINGS: "Settings",
}

# Widget-Zuordnung je Seite (Region → Widget-IDs).
_LAYOUTS: dict[Page, dict[str, tuple[str, ...]]] = {
    Page.OVERVIEW: {
        "left": ("watchlist", "recommendation_feed"),
        "center": ("overview_kpis",),
        "right": ("system_status",),
    },
    Page.LIVE_ANALYSIS: {
        "left": ("recommendation_feed",),
        "center": ("watchlist",),
        "right": ("live_reasons", "system_status"),
    },
    Page.PAPER_PORTFOLIO: {
        "left": ("recommendation_feed",),
        "center": ("portfolio_kpis", "portfolio_equity"),
        "right": ("system_status",),
    },
    Page.BACKTESTING: {
        "center": ("backtest_kpis", "backtest_equity", "backtest_trades"),
        "right": ("system_status",),
    },
    Page.ANALYTICS: {
        "center": (
            "analytics_long_short",
            "analytics_strategy",
            "analytics_pattern",
            "analytics_recommendation",
        ),
        "right": (
            "analytics_risk",
            "analytics_market",
            "analytics_time",
            "analytics_journal",
        ),
    },
    Page.PERFORMANCE: {
        "center": (
            "performance_equity",
            "performance_drawdown",
            "performance_profit_distribution",
            "performance_holding_time",
        ),
        "right": ("performance_returns", "system_status"),
    },
    Page.TRADE_JOURNAL: {
        "center": ("journal_table",),
        "right": ("system_status",),
    },
    Page.RECOMMENDATIONS: {
        "center": ("recommendations_table",),
        "right": ("system_status",),
    },
    Page.SETTINGS: {
        "center": ("settings_panel",),
    },
}

# Tastenkürzel (nur Navigation/Refresh – keine Fachlogik).
KEYBOARD_SHORTCUTS: dict[str, str] = {
    "F5": "refresh",
    "Ctrl+1": Page.OVERVIEW.value,
    "Ctrl+2": Page.ANALYTICS.value,
    "Ctrl+3": Page.PAPER_PORTFOLIO.value,
    "Ctrl+4": Page.BACKTESTING.value,
    "Ctrl+5": Page.TRADE_JOURNAL.value,
}


def build_default_router() -> Router:
    """Erzeugt einen Router mit allen neun Standard-Seiten."""
    router = Router()
    for page, title in _TITLES.items():
        router.register(
            PageLayout(
                page=page, title=title, icon=page.value, regions=dict(_LAYOUTS.get(page, {}))
            )
        )
    return router
