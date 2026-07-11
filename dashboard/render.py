"""Dünne Streamlit-Renderschicht (die einzige Stelle mit Streamlit-Import).

Diese Schicht **zeichnet** ausschließlich die bereits fertigen
:class:`~models.dashboard.WidgetSpec`-Beschreibungen. Sie enthält **keine**
Fachlogik, **keine** Berechnung und **keine** Datenveränderung. Fehlt
Streamlit in der Umgebung, wird diese Datei schlicht nicht importiert (die
gesamte Logik des Dashboards ist Streamlit-frei und testbar).
"""

from __future__ import annotations

from dashboard.theme import Theme
from models.dashboard import (
    KIND_CARDS,
    KIND_CHART,
    KIND_LIST,
    KIND_STATUS,
    KIND_TABLE,
    KIND_TEXT,
    ChartSpec,
    DashboardView,
    WidgetSpec,
)


def render_view(view: DashboardView, theme: Theme) -> None:  # pragma: no cover - UI-Glue
    """Rendert eine komplette Dashboard-Ansicht in Streamlit."""
    import streamlit as st

    st.markdown(f"### {view.title}")
    columns = st.columns(max(len(view.regions), 1))
    for column, region in zip(columns, ("left", "center", "right"), strict=False):
        with column:
            for widget_id in view.regions.get(region, ()):  # type: ignore[union-attr]
                spec = view.widgets.get(widget_id)
                if spec is not None:
                    render_widget(spec, theme)


def render_widget(spec: WidgetSpec, theme: Theme) -> None:  # pragma: no cover - UI-Glue
    """Rendert ein einzelnes Widget anhand seiner Beschreibung."""
    import streamlit as st

    st.caption(spec.title)
    if spec.placeholder:
        st.info(spec.text or "Keine Daten.")
        return
    if spec.kind == KIND_CARDS:
        for card in spec.cards:
            st.metric(card.label, card.value, card.delta)
    elif spec.kind == KIND_STATUS:
        for item in spec.status_items:
            st.write(f"{item.name}: {item.status}")
    elif spec.kind == KIND_TABLE and spec.table is not None:
        st.table(
            {col: [row[i] for row in spec.table.rows] for i, col in enumerate(spec.table.columns)}
        )
    elif spec.kind == KIND_CHART and spec.chart is not None:
        _render_chart(spec.chart, theme)
    elif spec.kind in (KIND_LIST, KIND_TEXT):
        if spec.text:
            st.write(spec.text)
        for item in spec.items:
            st.write(item)


def _render_chart(chart: ChartSpec, theme: Theme) -> None:  # pragma: no cover - UI-Glue
    """Rendert einen Chart (nur Darstellung der vorhandenen Werte)."""
    import streamlit as st

    if chart.is_empty:
        st.info("Keine Daten.")
        return
    data = {series.name or "series": list(series.values) for series in chart.series}
    if chart.chart_type in ("line", "area"):
        st.line_chart(data)
    elif chart.chart_type == "bar":
        st.bar_chart(data)
    else:
        st.write(data)
