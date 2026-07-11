"""Tests der Dashboard-Präsentationsmodelle (unveränderlich, keine Berechnung)."""

from __future__ import annotations

import dataclasses

import pytest

from models.dashboard import (
    KIND_CARDS,
    KIND_CHART,
    KIND_LIST,
    KIND_STATUS,
    KIND_TABLE,
    KIND_TEXT,
    TONE_ACCENT,
    TONE_DANGER,
    TONE_INFO,
    TONE_NEUTRAL,
    TONE_SUCCESS,
    TONE_WARNING,
    ChartSeries,
    ChartSpec,
    DashboardView,
    MetricCard,
    StatusItem,
    TableSpec,
    WidgetSpec,
)


def test_metric_card_defaults():
    card = MetricCard(label="PnL", value="10 €")
    assert card.tone == TONE_NEUTRAL
    assert card.delta is None
    assert card.icon == ""


def test_metric_card_is_frozen():
    card = MetricCard(label="PnL", value="10 €")
    with pytest.raises(dataclasses.FrozenInstanceError):
        card.value = "20 €"  # type: ignore[misc]


def test_status_item_defaults():
    item = StatusItem(name="Engine", status="online")
    assert item.tone == TONE_NEUTRAL


def test_chart_series_defaults():
    series = ChartSeries(name="Equity")
    assert series.values == ()
    assert series.color == ""


def test_chart_spec_is_empty_true_without_values():
    spec = ChartSpec(chart_id="c", chart_type="line", series=(ChartSeries("x"),))
    assert spec.is_empty is True


def test_chart_spec_is_empty_false_with_values():
    spec = ChartSpec(chart_id="c", chart_type="line", series=(ChartSeries("x", (1.0, 2.0)),))
    assert spec.is_empty is False


def test_chart_spec_no_series_is_empty():
    spec = ChartSpec(chart_id="c", chart_type="line")
    assert spec.is_empty is True


def test_table_spec_is_empty():
    assert TableSpec().is_empty is True
    assert TableSpec(columns=("A",), rows=(("1",),)).is_empty is False


def test_widget_spec_defaults():
    spec = WidgetSpec(widget_id="w", title="W", kind=KIND_CARDS)
    assert spec.cards == ()
    assert spec.chart is None
    assert spec.table is None
    assert spec.placeholder is False
    assert spec.warnings == ()
    assert spec.metadata == {}


def test_widget_spec_is_frozen():
    spec = WidgetSpec(widget_id="w", title="W", kind=KIND_CARDS)
    with pytest.raises(dataclasses.FrozenInstanceError):
        spec.title = "X"  # type: ignore[misc]


def test_dashboard_view_widget_lookup():
    spec = WidgetSpec(widget_id="w", title="W", kind=KIND_TEXT)
    view = DashboardView(page="overview", title="Overview", widgets={"w": spec})
    assert view.widget("w") is spec
    assert view.widget("missing") is None


def test_dashboard_view_widget_ids_ordered():
    view = DashboardView(
        page="overview",
        title="Overview",
        regions={"right": ("c",), "left": ("a",), "center": ("b",)},
    )
    assert view.widget_ids == ("a", "b", "c")


def test_dashboard_view_defaults():
    view = DashboardView(page="p", title="T")
    assert view.regions == {}
    assert view.widgets == {}
    assert view.device_class == "desktop"
    assert view.valid is True
    assert view.warnings == ()
    assert view.generated_at is None


def test_tone_constants_distinct():
    tones = {
        TONE_NEUTRAL,
        TONE_SUCCESS,
        TONE_DANGER,
        TONE_WARNING,
        TONE_INFO,
        TONE_ACCENT,
    }
    assert len(tones) == 6


def test_kind_constants_distinct():
    kinds = {KIND_CARDS, KIND_CHART, KIND_TABLE, KIND_STATUS, KIND_LIST, KIND_TEXT}
    assert len(kinds) == 6


def test_widget_spec_carries_status_items():
    item = StatusItem("Engine", "online", TONE_SUCCESS)
    spec = WidgetSpec(widget_id="s", title="S", kind=KIND_STATUS, status_items=(item,))
    assert spec.status_items[0].name == "Engine"


def test_widget_spec_carries_chart_and_table():
    chart = ChartSpec(chart_id="c", chart_type=KIND_CHART)
    table = TableSpec(columns=("A",), rows=(("1",),))
    spec = WidgetSpec(widget_id="w", title="W", kind=KIND_TABLE, chart=chart, table=table)
    assert spec.chart is chart
    assert spec.table is table
