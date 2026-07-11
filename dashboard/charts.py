"""Chart-Beschreibungen (Specs) für das Dashboard.

Diese Funktionen bauen aus **bereits vorhandenen** Werten eine
:class:`~models.dashboard.ChartSpec`. Sie **rechnen nichts** – sie übernehmen die
Daten unverändert und legen nur Typ, Achsen und Farben (aus dem Theme) fest. Das
eigentliche Zeichnen übernimmt die dünne Streamlit-Schicht.

Erlaubte Farben sind ausschließlich die Chart-Palette des Themes
(Schwarz-Hintergrund, Gold, Grün, Rot, Cyan).
"""

from __future__ import annotations

from collections.abc import Sequence

from dashboard.theme import Theme
from models.dashboard import ChartSeries, ChartSpec

LINE = "line"
AREA = "area"
BAR = "bar"
DONUT = "donut"
HEATMAP = "heatmap"


def _labels(x_labels: Sequence[str] | None, length: int) -> tuple[str, ...]:
    """Übernimmt Achsenbeschriftungen oder erzeugt fortlaufende Indizes (Anzeige)."""
    if x_labels is not None:
        return tuple(str(label) for label in x_labels)
    return tuple(str(i) for i in range(length))


def line_chart(
    chart_id: str,
    values: Sequence[float],
    theme: Theme,
    x_labels: Sequence[str] | None = None,
    name: str = "",
    x_label: str = "",
    y_label: str = "",
) -> ChartSpec:
    """Baut einen Linien-Chart aus vorhandenen Werten."""
    series = ChartSeries(
        name=name, values=tuple(float(v) for v in values), color=theme.chart_palette[0]
    )
    return ChartSpec(
        chart_id=chart_id,
        chart_type=LINE,
        series=(series,),
        x_labels=_labels(x_labels, len(series.values)),
        colors=theme.chart_palette,
        x_label=x_label,
        y_label=y_label,
    )


def area_chart(
    chart_id: str,
    values: Sequence[float],
    theme: Theme,
    x_labels: Sequence[str] | None = None,
    name: str = "",
    x_label: str = "",
    y_label: str = "",
) -> ChartSpec:
    """Baut einen Flächen-Chart aus vorhandenen Werten."""
    series = ChartSeries(
        name=name, values=tuple(float(v) for v in values), color=theme.chart_palette[0]
    )
    return ChartSpec(
        chart_id=chart_id,
        chart_type=AREA,
        series=(series,),
        x_labels=_labels(x_labels, len(series.values)),
        colors=theme.chart_palette,
        x_label=x_label,
        y_label=y_label,
    )


def bar_chart(
    chart_id: str,
    labels: Sequence[str],
    values: Sequence[float],
    theme: Theme,
    name: str = "",
    x_label: str = "",
    y_label: str = "",
) -> ChartSpec:
    """Baut einen Balken-Chart aus vorhandenen Kategorien/Werten."""
    series = ChartSeries(name=name, values=tuple(float(v) for v in values))
    return ChartSpec(
        chart_id=chart_id,
        chart_type=BAR,
        series=(series,),
        x_labels=tuple(str(label) for label in labels),
        colors=theme.chart_palette,
        x_label=x_label,
        y_label=y_label,
    )


def donut_chart(
    chart_id: str, labels: Sequence[str], values: Sequence[float], theme: Theme
) -> ChartSpec:
    """Baut einen Donut-Chart aus vorhandenen Anteilen."""
    series = ChartSeries(name="", values=tuple(float(v) for v in values))
    return ChartSpec(
        chart_id=chart_id,
        chart_type=DONUT,
        series=(series,),
        x_labels=tuple(str(label) for label in labels),
        colors=theme.chart_palette,
    )


def multi_series_chart(
    chart_id: str,
    chart_type: str,
    series: Sequence[ChartSeries],
    theme: Theme,
    x_labels: Sequence[str] | None = None,
    x_label: str = "",
    y_label: str = "",
) -> ChartSpec:
    """Baut einen Chart mit mehreren, bereits vorhandenen Datenreihen."""
    length = max((len(s.values) for s in series), default=0)
    return ChartSpec(
        chart_id=chart_id,
        chart_type=chart_type,
        series=tuple(series),
        x_labels=_labels(x_labels, length),
        colors=theme.chart_palette,
        x_label=x_label,
        y_label=y_label,
    )
