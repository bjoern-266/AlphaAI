"""Domänenmodell: Dashboard-Präsentationstypen.

Enthält die unveränderlichen **Anzeige**-Datentypen des AlphaAI Command Center.
Das Dashboard ist **ausschließlich** Presentation Layer: diese Typen tragen nur
bereits berechnete, anzeigefertige Werte aus den bestehenden Reports. Es findet
**keine** Berechnung, **keine** Fachlogik und **keine** Veränderung von Daten
statt.

Enthaltene Typen:

* :class:`MetricCard` – eine Kennzahl-Kachel (Wert bereits als Text formatiert),
* :class:`StatusItem` – ein System-Status-Eintrag,
* :class:`ChartSeries` / :class:`ChartSpec` – eine reine Chart-Beschreibung
  (Daten + Farben; das eigentliche Zeichnen macht die Streamlit-Schicht),
* :class:`TableSpec` – eine Tabellen-Beschreibung (Spalten + Zeilen als Text),
* :class:`WidgetSpec` – die Ausgabe eines Widgets (was angezeigt werden soll),
* :class:`DashboardView` – die zusammengesetzte Seite (Regionen → Widgets).

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.analytics`) bzw. die Standardbibliothek – **kein** Import
aus ``engines``, ``dashboard`` o. Ä. Die Aufbereitung (Reports → View Models →
Widgets) liegt im Paket ``dashboard``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from models.analytics import GroupStatistics

# Anzeige-„Tönungen" (semantische Farbrolle, aufgelöst über das Theme).
TONE_NEUTRAL = "neutral"
TONE_SUCCESS = "success"
TONE_DANGER = "danger"
TONE_WARNING = "warning"
TONE_INFO = "info"
TONE_ACCENT = "accent"

# Widget-Arten (bestimmen, wie die Streamlit-Schicht rendert).
KIND_CARDS = "cards"
KIND_CHART = "chart"
KIND_TABLE = "table"
KIND_STATUS = "status"
KIND_LIST = "list"
KIND_TEXT = "text"


@dataclass(frozen=True, slots=True)
class MetricCard:
    """Eine Kennzahl-Kachel (unveränderlich, Wert bereits formatiert).

    Attributes:
        label: Beschriftung der Kennzahl.
        value: Anzeigewert als **fertiger Text** (z. B. ``"12.340,00 €"`` oder
            ``"—"`` bei fehlenden Daten).
        delta: Optionale Veränderungsangabe als Text (oder ``None``).
        tone: Semantische Tönung (``neutral``/``success``/``danger``/…).
        icon: Optionaler Icon-Name (aus dem Theme).
    """

    label: str
    value: str
    delta: str | None = None
    tone: str = TONE_NEUTRAL
    icon: str = ""


@dataclass(frozen=True, slots=True)
class StatusItem:
    """Ein System-Status-Eintrag (unveränderlich).

    Attributes:
        name: Name des Moduls (z. B. ``"Recommendation Engine"``).
        status: Status als Text (z. B. ``"online"``/``"offline"``/``"no_data"``).
        tone: Semantische Tönung.
    """

    name: str
    status: str
    tone: str = TONE_NEUTRAL


@dataclass(frozen=True, slots=True)
class ChartSeries:
    """Eine Datenreihe eines Charts (unveränderlich).

    Attributes:
        name: Name der Reihe.
        values: Bereits vorhandene Werte (aus dem Report übernommen).
        color: Optionale Farbe (aus dem Theme); leer = Standardpalette.
    """

    name: str
    values: tuple[float, ...] = ()
    color: str = ""


@dataclass(frozen=True, slots=True)
class ChartSpec:
    """Beschreibung eines Charts (unveränderlich) – **keine** Berechnung.

    Attributes:
        chart_id: Stabiler Bezeichner.
        chart_type: ``line``/``area``/``bar``/``donut``/``heatmap``.
        series: Datenreihen (übernommene Werte).
        x_labels: Beschriftungen der X-Achse (Text).
        colors: Farbpalette (aus dem Theme).
        x_label: Achsentitel X.
        y_label: Achsentitel Y.
        options: Zusätzliche Anzeigeoptionen.
    """

    chart_id: str
    chart_type: str
    series: tuple[ChartSeries, ...] = ()
    x_labels: tuple[str, ...] = ()
    colors: tuple[str, ...] = ()
    x_label: str = ""
    y_label: str = ""
    options: dict[str, Any] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        """Ob der Chart keine anzeigbaren Datenpunkte enthält."""
        return not any(series.values for series in self.series)


@dataclass(frozen=True, slots=True)
class TableSpec:
    """Beschreibung einer Tabelle (unveränderlich, Zellen als Text).

    Attributes:
        columns: Spaltenüberschriften.
        rows: Zeilen (jede Zeile eine Liste von Zell-Texten).
    """

    columns: tuple[str, ...] = ()
    rows: tuple[tuple[str, ...], ...] = ()

    @property
    def is_empty(self) -> bool:
        """Ob die Tabelle keine Zeilen enthält."""
        return not self.rows


@dataclass(frozen=True, slots=True)
class WidgetSpec:
    """Ausgabe eines Widgets (unveränderlich) – was angezeigt werden soll.

    Ein Widget liefert **nur** eine Beschreibung; das tatsächliche Rendern
    übernimmt die dünne Streamlit-Schicht. Fehlen Daten, ist ``placeholder``
    gesetzt (es wird ein „Keine Daten"-Zustand angezeigt, **keine**
    Ersatzberechnung).

    Attributes:
        widget_id: Stabiler Bezeichner des Widgets.
        title: Anzeigetitel.
        kind: Art des Widgets (``cards``/``chart``/``table``/``status``/…).
        cards: Kennzahl-Kacheln.
        chart: Optionale Chart-Beschreibung.
        table: Optionale Tabellen-Beschreibung.
        status_items: Status-Einträge.
        items: Freie Text-/Listeneinträge.
        text: Freitext (z. B. Summary).
        icon: Optionaler Icon-Name.
        placeholder: Ob keine Daten vorliegen (Leer-/No-Data-Zustand).
        warnings: Aus den Reports übernommene Warnungen.
        metadata: Zusatzinformationen.
    """

    widget_id: str
    title: str
    kind: str
    cards: tuple[MetricCard, ...] = ()
    chart: ChartSpec | None = None
    table: TableSpec | None = None
    status_items: tuple[StatusItem, ...] = ()
    items: tuple[str, ...] = ()
    text: str = ""
    icon: str = ""
    placeholder: bool = False
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class DashboardView:
    """Die zusammengesetzte Dashboard-Seite (unveränderlich).

    Attributes:
        page: Name der aktiven Seite.
        title: Anzeigetitel der Seite.
        regions: Zuordnung Region (``left``/``center``/``right``) → Widget-IDs.
        widgets: Zuordnung Widget-ID → :class:`WidgetSpec`.
        device_class: Aktive Geräteklasse (Responsive-Layout).
        valid: Ob die Seite grundsätzlich anzeigbar ist.
        warnings: Gesammelte Warnungen.
        generated_at: Erstellungszeitpunkt der Ansicht.
    """

    page: str
    title: str
    regions: dict[str, tuple[str, ...]] = field(default_factory=dict)
    widgets: dict[str, WidgetSpec] = field(default_factory=dict)
    device_class: str = "desktop"
    valid: bool = True
    warnings: tuple[str, ...] = ()
    generated_at: datetime | None = None

    def widget(self, widget_id: str) -> WidgetSpec | None:
        """Gibt die Widget-Beschreibung zu einer ID zurück (oder ``None``)."""
        return self.widgets.get(widget_id)

    @property
    def widget_ids(self) -> tuple[str, ...]:
        """Alle Widget-IDs der Seite in Regionen-Reihenfolge."""
        ordered: list[str] = []
        for region in ("left", "center", "right"):
            ordered.extend(self.regions.get(region, ()))
        return tuple(ordered)


# Für Analytics-Tabellen wird die bestehende, bereits berechnete
# :class:`~models.analytics.GroupStatistics` unverändert weitergereicht.
__all__ = [
    "MetricCard",
    "StatusItem",
    "ChartSeries",
    "ChartSpec",
    "TableSpec",
    "WidgetSpec",
    "DashboardView",
    "GroupStatistics",
    "TONE_NEUTRAL",
    "TONE_SUCCESS",
    "TONE_DANGER",
    "TONE_WARNING",
    "TONE_INFO",
    "TONE_ACCENT",
    "KIND_CARDS",
    "KIND_CHART",
    "KIND_TABLE",
    "KIND_STATUS",
    "KIND_LIST",
    "KIND_TEXT",
]
