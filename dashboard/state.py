"""Dashboard-State und Anzeige-Enums.

Der :class:`DashboardState` hält den **Anzeige**-Zustand des Command Center
(aktive Seite, Tabs, Filter, Sortierung, Zoom, Sidebar, Session, Chart-
Einstellungen, Refresh-Rate, Suche, Geräteklasse). Er enthält **keine**
Fachlogik und **keine** Berechnungen. Über :meth:`DashboardState.snapshot` und
:meth:`DashboardState.restore` lässt sich der Zustand vollständig sichern und
wiederherstellen, sodass er **nie verloren geht**.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class Page(Enum):
    """Die neun Dashboard-Seiten."""

    OVERVIEW = "overview"
    LIVE_ANALYSIS = "live_analysis"
    PAPER_PORTFOLIO = "paper_portfolio"
    BACKTESTING = "backtesting"
    ANALYTICS = "analytics"
    PERFORMANCE = "performance"
    TRADE_JOURNAL = "trade_journal"
    RECOMMENDATIONS = "recommendations"
    MARKET_INTELLIGENCE = "market_intelligence"
    MARKET_DISCOVERY = "market_discovery"
    LIVE_OPERATIONS = "live_operations"
    SETTINGS = "settings"


class RefreshRate(Enum):
    """Unterstützte Auto-Refresh-Raten in Sekunden (``0`` = manuell)."""

    MANUAL = 0
    SECOND_1 = 1
    SECOND_5 = 5
    SECOND_15 = 15
    SECOND_30 = 30
    SECOND_60 = 60


class DeviceClass(Enum):
    """Ziel-Geräteklassen (Responsive-Layout; Smartphone ist kein Ziel)."""

    DESKTOP = "desktop"
    TABLET = "tablet"
    ULTRAWIDE = "ultrawide"
    UHD_4K = "uhd_4k"


class LoadingState(Enum):
    """Ladezustände (Skeleton/Progress/Fade – nie leere Seiten)."""

    IDLE = "idle"
    SKELETON = "skeleton"
    PROGRESS = "progress"
    FADE = "fade"


class ErrorState(Enum):
    """Fehler-/Verbindungszustände (keine Exceptions im Frontend)."""

    NONE = "none"
    LOADING = "loading"
    OFFLINE = "offline"
    NO_DATA = "no_data"
    DISCONNECTED = "disconnected"
    TIMEOUT = "timeout"
    ERROR = "error"


class SystemStatus(Enum):
    """Status eines Moduls in der System-Status-Anzeige."""

    ONLINE = "online"
    OFFLINE = "offline"
    NO_DATA = "no_data"
    DEGRADED = "degraded"


class DashboardState:
    """Hält den Anzeige-Zustand des Dashboards (kein Fachwissen).

    Args:
        active_page: Startseite.
        device_class: Startgeräteklasse.
        refresh_rate: Start-Refresh-Rate.
    """

    def __init__(
        self,
        active_page: Page = Page.OVERVIEW,
        device_class: DeviceClass = DeviceClass.DESKTOP,
        refresh_rate: RefreshRate = RefreshRate.MANUAL,
    ) -> None:
        self.active_page = active_page
        self.device_class = device_class
        self.refresh_rate = refresh_rate
        self.sidebar_collapsed = False
        self.search_query = ""
        self.loading_state = LoadingState.IDLE
        self.error_state = ErrorState.NONE
        self.active_tabs: dict[str, str] = {}
        self.filters: dict[str, Any] = {}
        self.sort: dict[str, tuple[str, bool]] = {}
        self.zoom: dict[str, float] = {}
        self.session: dict[str, Any] = {}
        self.chart_settings: dict[str, Any] = {}

    # -- Navigation ----------------------------------------------------- #

    def set_page(self, page: Page) -> None:
        """Setzt die aktive Seite."""
        self.active_page = page

    def set_tab(self, page: Page, tab: str) -> None:
        """Merkt den aktiven Tab einer Seite."""
        self.active_tabs[page.value] = tab

    def get_tab(self, page: Page, default: str = "") -> str:
        """Gibt den aktiven Tab einer Seite zurück."""
        return self.active_tabs.get(page.value, default)

    # -- Filter / Sortierung / Zoom ------------------------------------- #

    def set_filter(self, key: str, value: Any) -> None:
        """Setzt einen Anzeigefilter."""
        self.filters[key] = value

    def get_filter(self, key: str, default: Any = None) -> Any:
        """Liest einen Anzeigefilter."""
        return self.filters.get(key, default)

    def clear_filter(self, key: str) -> None:
        """Entfernt einen Filter (falls vorhanden)."""
        self.filters.pop(key, None)

    def set_sort(self, key: str, column: str, ascending: bool = True) -> None:
        """Setzt eine Sortierung (Spalte + Richtung)."""
        self.sort[key] = (column, ascending)

    def get_sort(self, key: str) -> tuple[str, bool] | None:
        """Liest die Sortierung zu einem Schlüssel."""
        return self.sort.get(key)

    def set_zoom(self, key: str, level: float) -> None:
        """Setzt den Zoom eines Charts."""
        self.zoom[key] = level

    # -- Sidebar / Suche / Refresh / Gerät ------------------------------ #

    def toggle_sidebar(self) -> bool:
        """Klappt die Sidebar um und gibt den neuen Zustand zurück."""
        self.sidebar_collapsed = not self.sidebar_collapsed
        return self.sidebar_collapsed

    def set_search(self, query: str) -> None:
        """Setzt die globale Suchanfrage."""
        self.search_query = query

    def set_refresh_rate(self, rate: RefreshRate) -> None:
        """Setzt die Auto-Refresh-Rate."""
        self.refresh_rate = rate

    def set_device(self, device_class: DeviceClass) -> None:
        """Setzt die aktive Geräteklasse."""
        self.device_class = device_class

    def set_chart_setting(self, key: str, value: Any) -> None:
        """Merkt eine Chart-Anzeigeoption."""
        self.chart_settings[key] = value

    # -- Persistenz (State geht nie verloren) --------------------------- #

    def snapshot(self) -> dict[str, Any]:
        """Erzeugt eine vollständige, serialisierbare Kopie des Zustands."""
        return {
            "active_page": self.active_page.value,
            "device_class": self.device_class.value,
            "refresh_rate": self.refresh_rate.value,
            "sidebar_collapsed": self.sidebar_collapsed,
            "search_query": self.search_query,
            "loading_state": self.loading_state.value,
            "error_state": self.error_state.value,
            "active_tabs": dict(self.active_tabs),
            "filters": dict(self.filters),
            "sort": {k: list(v) for k, v in self.sort.items()},
            "zoom": dict(self.zoom),
            "session": dict(self.session),
            "chart_settings": dict(self.chart_settings),
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Stellt einen zuvor gesicherten Zustand wieder her."""
        self.active_page = Page(snapshot.get("active_page", self.active_page.value))
        self.device_class = DeviceClass(snapshot.get("device_class", self.device_class.value))
        self.refresh_rate = RefreshRate(snapshot.get("refresh_rate", self.refresh_rate.value))
        self.sidebar_collapsed = bool(snapshot.get("sidebar_collapsed", self.sidebar_collapsed))
        self.search_query = str(snapshot.get("search_query", self.search_query))
        self.loading_state = LoadingState(snapshot.get("loading_state", self.loading_state.value))
        self.error_state = ErrorState(snapshot.get("error_state", self.error_state.value))
        self.active_tabs = dict(snapshot.get("active_tabs", {}))
        self.filters = dict(snapshot.get("filters", {}))
        self.sort = {k: tuple(v) for k, v in snapshot.get("sort", {}).items()}
        self.zoom = dict(snapshot.get("zoom", {}))
        self.session = dict(snapshot.get("session", {}))
        self.chart_settings = dict(snapshot.get("chart_settings", {}))
