"""Laden der Dashboard-Anzeigeeinstellungen.

Liest ``dashboard/settings.toml`` (**nur** Anzeigeoptionen) in eine
unveränderliche :class:`DashboardSettings`. Es gibt hier **keine**
Handelsparameter und **keine** Fachlogik.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from core.exceptions import AlphaAIError
from core.paths import PROJECT_ROOT

DASHBOARD_SETTINGS_FILE = PROJECT_ROOT / "dashboard" / "settings.toml"


class DashboardSettingsError(AlphaAIError):
    """Wird ausgelöst, wenn die Dashboard-Einstellungen ungültig sind."""


@dataclass(frozen=True, slots=True)
class DashboardSettings:
    """Anzeigeoptionen des Dashboards (unveränderlich).

    Attributes:
        default_page: Start-Seite (Slug).
        dark_mode: Ob Dark Mode aktiv ist.
        default_device: Start-Geräteklasse.
        sidebar_collapsed: Ob die Sidebar eingeklappt startet.
        default_refresh_seconds: Standard-Refresh (0 = manuell).
        refresh_options: Auswählbare Auto-Refresh-Raten (Sekunden).
        chart_default_type: Standard-Charttyp.
        chart_show_grid: Ob Chart-Gitter angezeigt wird.
        chart_animate: Ob Charts animiert werden.
        table_page_size: Zeilen pro Tabellenseite.
        default_direction_filter: Standard-Richtungsfilter.
        default_strength_filter: Standard-Stärkefilter.
        export_formats: Angebotene Export-Formate.
    """

    default_page: str = "overview"
    dark_mode: bool = True
    default_device: str = "desktop"
    sidebar_collapsed: bool = False
    default_refresh_seconds: int = 0
    refresh_options: tuple[int, ...] = (1, 5, 15, 30, 60)
    chart_default_type: str = "line"
    chart_show_grid: bool = True
    chart_animate: bool = True
    table_page_size: int = 25
    default_direction_filter: str = "all"
    default_strength_filter: str = "all"
    export_formats: tuple[str, ...] = ("csv", "excel", "pdf", "png")
    metadata: dict[str, str] = field(default_factory=dict)


def load_dashboard_settings(path: Path | None = None) -> DashboardSettings:
    """Lädt die Dashboard-Einstellungen aus der TOML-Datei.

    Raises:
        DashboardSettingsError: Wenn die Datei fehlt oder ungültig ist.
    """
    settings_path = path or DASHBOARD_SETTINGS_FILE
    if not settings_path.is_file():
        raise DashboardSettingsError(f"Dashboard-Einstellungen nicht gefunden: {settings_path}")
    try:
        with settings_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise DashboardSettingsError(
            f"Dashboard-Einstellungen sind kein gültiges TOML: {error}"
        ) from error
    return load_dashboard_settings_from_dict(data)


def load_dashboard_settings_from_dict(data: dict) -> DashboardSettings:
    """Baut :class:`DashboardSettings` aus einer geparsten TOML-Struktur.

    Raises:
        DashboardSettingsError: Wenn Werte strukturell ungültig sind.
    """
    display = data.get("display", {})
    refresh = data.get("refresh", {})
    charts = data.get("charts", {})
    tables = data.get("tables", {})
    filters = data.get("filters", {})
    export = data.get("export", {})

    options = tuple(int(v) for v in refresh.get("options_seconds", [1, 5, 15, 30, 60]))
    default_refresh = int(refresh.get("default_seconds", 0))
    if default_refresh != 0 and default_refresh not in options:
        raise DashboardSettingsError(
            f"[refresh].default_seconds={default_refresh} ist keine gültige Option."
        )
    page_size = int(tables.get("page_size", 25))
    if page_size < 1:
        raise DashboardSettingsError("[tables].page_size muss mindestens 1 sein.")

    return DashboardSettings(
        default_page=str(display.get("default_page", "overview")),
        dark_mode=bool(display.get("dark_mode", True)),
        default_device=str(display.get("default_device", "desktop")),
        sidebar_collapsed=bool(display.get("sidebar_collapsed", False)),
        default_refresh_seconds=default_refresh,
        refresh_options=options,
        chart_default_type=str(charts.get("default_type", "line")),
        chart_show_grid=bool(charts.get("show_grid", True)),
        chart_animate=bool(charts.get("animate", True)),
        table_page_size=page_size,
        default_direction_filter=str(filters.get("default_direction", "all")),
        default_strength_filter=str(filters.get("default_strength", "all")),
        export_formats=tuple(str(f) for f in export.get("formats", ["csv", "excel", "pdf", "png"])),
    )
