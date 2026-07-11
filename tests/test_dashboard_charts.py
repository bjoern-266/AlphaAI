"""Tests der Chart-Beschreibungen (übernehmen Werte, rechnen nicht)."""

from __future__ import annotations

from dashboard import charts
from dashboard.theme import load_theme
from models.dashboard import ChartSeries

THEME = load_theme()


def test_line_chart_type_and_values():
    spec = charts.line_chart("eq", [1.0, 2.0, 3.0], THEME)
    assert spec.chart_type == charts.LINE
    assert spec.series[0].values == (1.0, 2.0, 3.0)


def test_line_chart_uses_theme_palette():
    spec = charts.line_chart("eq", [1.0], THEME)
    assert spec.colors == THEME.chart_palette
    assert spec.series[0].color == THEME.chart_palette[0]


def test_line_chart_generates_index_labels():
    spec = charts.line_chart("eq", [1.0, 2.0], THEME)
    assert spec.x_labels == ("0", "1")


def test_line_chart_custom_labels():
    spec = charts.line_chart("eq", [1.0, 2.0], THEME, x_labels=["Mon", "Tue"])
    assert spec.x_labels == ("Mon", "Tue")


def test_area_chart_type():
    spec = charts.area_chart("eq", [1.0], THEME)
    assert spec.chart_type == charts.AREA


def test_bar_chart_labels_and_values():
    spec = charts.bar_chart("dist", ["A", "B"], [10.0, 20.0], THEME)
    assert spec.chart_type == charts.BAR
    assert spec.x_labels == ("A", "B")
    assert spec.series[0].values == (10.0, 20.0)


def test_donut_chart():
    spec = charts.donut_chart("ls", ["LONG", "SHORT"], [5, 3], THEME)
    assert spec.chart_type == charts.DONUT
    assert spec.x_labels == ("LONG", "SHORT")
    assert spec.series[0].values == (5.0, 3.0)


def test_multi_series_chart():
    a = ChartSeries("A", (1.0, 2.0))
    b = ChartSeries("B", (3.0, 4.0, 5.0))
    spec = charts.multi_series_chart("m", charts.LINE, [a, b], THEME)
    assert len(spec.series) == 2
    # Labels folgen der längsten Reihe.
    assert spec.x_labels == ("0", "1", "2")


def test_empty_values_chart_is_empty():
    spec = charts.line_chart("eq", [], THEME)
    assert spec.is_empty is True


def test_chart_values_are_floats():
    spec = charts.line_chart("eq", [1, 2, 3], THEME)
    assert all(isinstance(v, float) for v in spec.series[0].values)


def test_multi_series_empty_default_length():
    spec = charts.multi_series_chart("m", charts.LINE, [], THEME)
    assert spec.x_labels == ()
    assert spec.is_empty is True


def test_line_chart_axis_titles():
    spec = charts.line_chart("eq", [1.0], THEME, x_label="Zeit", y_label="Equity")
    assert spec.x_label == "Zeit"
    assert spec.y_label == "Equity"
