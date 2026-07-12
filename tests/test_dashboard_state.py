"""Tests des Dashboard-Zustands (Anzeige-Zustand, geht nie verloren)."""

from __future__ import annotations

from dashboard.state import (
    DashboardState,
    DeviceClass,
    ErrorState,
    LoadingState,
    Page,
    RefreshRate,
    SystemStatus,
)


def test_default_state():
    state = DashboardState()
    assert state.active_page is Page.OVERVIEW
    assert state.device_class is DeviceClass.DESKTOP
    assert state.refresh_rate is RefreshRate.MANUAL
    assert state.loading_state is LoadingState.IDLE
    assert state.error_state is ErrorState.NONE
    assert state.sidebar_collapsed is False
    assert state.search_query == ""


def test_all_pages_defined():
    assert len(list(Page)) == 12


def test_refresh_rates_values():
    assert {r.value for r in RefreshRate} == {0, 1, 5, 15, 30, 60}


def test_device_classes():
    assert {d.value for d in DeviceClass} == {"desktop", "tablet", "ultrawide", "uhd_4k"}


def test_error_states():
    assert {e.value for e in ErrorState} == {
        "none",
        "loading",
        "offline",
        "no_data",
        "disconnected",
        "timeout",
        "error",
    }


def test_system_status_values():
    assert {s.value for s in SystemStatus} == {"online", "offline", "no_data", "degraded"}


def test_set_page():
    state = DashboardState()
    state.set_page(Page.ANALYTICS)
    assert state.active_page is Page.ANALYTICS


def test_tabs_roundtrip():
    state = DashboardState()
    state.set_tab(Page.ANALYTICS, "strategies")
    assert state.get_tab(Page.ANALYTICS) == "strategies"
    assert state.get_tab(Page.BACKTESTING, "default") == "default"


def test_filter_set_get_clear():
    state = DashboardState()
    state.set_filter("direction", "long")
    assert state.get_filter("direction") == "long"
    state.clear_filter("direction")
    assert state.get_filter("direction", "all") == "all"


def test_clear_missing_filter_is_safe():
    state = DashboardState()
    state.clear_filter("nope")  # darf nicht werfen
    assert state.get_filter("nope") is None


def test_sort_set_get():
    state = DashboardState()
    state.set_sort("journal", "pnl", ascending=False)
    assert state.get_sort("journal") == ("pnl", False)
    assert state.get_sort("missing") is None


def test_zoom():
    state = DashboardState()
    state.set_zoom("equity", 1.5)
    assert state.zoom["equity"] == 1.5


def test_sidebar_toggle():
    state = DashboardState()
    assert state.toggle_sidebar() is True
    assert state.sidebar_collapsed is True
    assert state.toggle_sidebar() is False


def test_search():
    state = DashboardState()
    state.set_search("AAPL")
    assert state.search_query == "AAPL"


def test_set_refresh_rate():
    state = DashboardState()
    state.set_refresh_rate(RefreshRate.SECOND_15)
    assert state.refresh_rate is RefreshRate.SECOND_15


def test_set_device():
    state = DashboardState()
    state.set_device(DeviceClass.ULTRAWIDE)
    assert state.device_class is DeviceClass.ULTRAWIDE


def test_chart_setting():
    state = DashboardState()
    state.set_chart_setting("show_grid", False)
    assert state.chart_settings["show_grid"] is False


def test_snapshot_contains_all_keys():
    snap = DashboardState().snapshot()
    for key in (
        "active_page",
        "device_class",
        "refresh_rate",
        "sidebar_collapsed",
        "search_query",
        "loading_state",
        "error_state",
        "active_tabs",
        "filters",
        "sort",
        "zoom",
        "session",
        "chart_settings",
    ):
        assert key in snap


def test_snapshot_restore_roundtrip():
    state = DashboardState()
    state.set_page(Page.PERFORMANCE)
    state.set_device(DeviceClass.UHD_4K)
    state.set_refresh_rate(RefreshRate.SECOND_30)
    state.toggle_sidebar()
    state.set_search("TSLA")
    state.set_tab(Page.ANALYTICS, "risk")
    state.set_filter("direction", "short")
    state.set_sort("journal", "time", ascending=False)
    state.set_zoom("equity", 2.0)
    state.set_chart_setting("animate", False)
    state.session["scroll"] = 120
    snap = state.snapshot()

    restored = DashboardState()
    restored.restore(snap)
    assert restored.active_page is Page.PERFORMANCE
    assert restored.device_class is DeviceClass.UHD_4K
    assert restored.refresh_rate is RefreshRate.SECOND_30
    assert restored.sidebar_collapsed is True
    assert restored.search_query == "TSLA"
    assert restored.get_tab(Page.ANALYTICS) == "risk"
    assert restored.get_filter("direction") == "short"
    assert restored.get_sort("journal") == ("time", False)
    assert restored.zoom["equity"] == 2.0
    assert restored.chart_settings["animate"] is False
    assert restored.session["scroll"] == 120


def test_restore_from_empty_keeps_defaults():
    state = DashboardState()
    state.restore({})
    assert state.active_page is Page.OVERVIEW
    assert state.device_class is DeviceClass.DESKTOP


def test_snapshot_is_serializable_types():
    snap = DashboardState().snapshot()
    # active_page etc. sind bereits primitive Werte (Strings/Ints), kein Enum.
    assert isinstance(snap["active_page"], str)
    assert isinstance(snap["refresh_rate"], int)


def test_restore_preserves_loading_and_error_states():
    state = DashboardState()
    state.loading_state = LoadingState.PROGRESS
    state.error_state = ErrorState.TIMEOUT
    snap = state.snapshot()
    restored = DashboardState()
    restored.restore(snap)
    assert restored.loading_state is LoadingState.PROGRESS
    assert restored.error_state is ErrorState.TIMEOUT


def test_snapshot_is_independent_copy():
    state = DashboardState()
    state.set_filter("a", 1)
    snap = state.snapshot()
    state.set_filter("a", 2)
    # Der Snapshot darf sich nicht nachträglich ändern.
    assert snap["filters"]["a"] == 1
