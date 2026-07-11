"""Tests der DashboardEngine (setzt Ansichten zusammen, berechnet nichts)."""

from __future__ import annotations

import pytest

from dashboard.engine import DashboardEngine
from dashboard.router import PageLayout, Router, build_default_router
from dashboard.settings import DashboardSettings
from dashboard.state import (
    DashboardState,
    DeviceClass,
    ErrorState,
    LoadingState,
    Page,
)
from dashboard.theme import load_theme
from dashboard.viewmodels import ReportBundle
from dashboard.widget_registry import WidgetRegistry, build_default_registry
from dashboard.widgets.base import BaseWidget
from engines.indicator_result import IndicatorResult
from models.dashboard import KIND_TEXT, DashboardView, WidgetSpec
from tests.dashboard_helpers import (
    make_analytics_report,
    make_backtest_report,
    make_paper_report,
    make_recommendation_report,
)


def _engine() -> DashboardEngine:
    return DashboardEngine(theme=load_theme(), settings=DashboardSettings())


def _full_bundle() -> ReportBundle:
    return ReportBundle(
        recommendation=make_recommendation_report(),
        paper_trading=make_paper_report(),
        backtest=make_backtest_report(),
        analytics=make_analytics_report(),
        indicator=IndicatorResult(outputs={}, valid=True, metadata={}),
    )


def test_from_config_builds_engine():
    engine = DashboardEngine.from_config()
    assert isinstance(engine, DashboardEngine)
    assert engine.router.has(Page.OVERVIEW)


@pytest.mark.parametrize("page", list(Page))
def test_build_view_for_every_page(page):
    engine = _engine()
    state = DashboardState(active_page=page)
    view = engine.build_view(state, _full_bundle())
    assert isinstance(view, DashboardView)
    assert view.page == page.value
    assert view.valid is True
    assert view.widgets


def test_build_view_empty_bundle_still_valid():
    engine = _engine()
    view = engine.build_view(DashboardState(), ReportBundle())
    # Keine Reports -> Widgets zeigen Platzhalter, aber die Seite ist gültig.
    assert view.valid is True
    assert all(isinstance(w, WidgetSpec) for w in view.widgets.values())


def test_loading_state_shows_loading_view():
    engine = _engine()
    state = DashboardState()
    state.loading_state = LoadingState.SKELETON
    view = engine.build_view(state, _full_bundle())
    assert list(view.widgets) == ["loading_state"]
    assert view.valid is False


def test_error_state_shows_error_view():
    engine = _engine()
    state = DashboardState()
    state.error_state = ErrorState.OFFLINE
    view = engine.build_view(state, ReportBundle())
    assert list(view.widgets) == ["error_state"]
    assert view.valid is False


def test_loading_takes_priority_over_error():
    engine = _engine()
    state = DashboardState()
    state.loading_state = LoadingState.PROGRESS
    state.error_state = ErrorState.OFFLINE
    view = engine.build_view(state, ReportBundle())
    assert list(view.widgets) == ["loading_state"]


def test_generated_at_is_set():
    engine = _engine()
    view = engine.build_view(DashboardState(), _full_bundle())
    assert view.generated_at is not None


def test_device_class_recorded_in_view():
    engine = _engine()
    state = DashboardState(device_class=DeviceClass.ULTRAWIDE)
    view = engine.build_view(state, _full_bundle())
    assert view.device_class == "ultrawide"


def test_tablet_layout_single_column():
    engine = _engine()
    state = DashboardState(device_class=DeviceClass.TABLET)
    view = engine.build_view(state, _full_bundle())
    assert set(view.regions) == {"center"}


def test_unregistered_widget_produces_warning_not_exception():
    router = Router()
    router.register(PageLayout(Page.OVERVIEW, "Overview", "radar", {"center": ("ghost_widget",)}))
    engine = DashboardEngine(
        theme=load_theme(),
        settings=DashboardSettings(),
        registry=build_default_registry(),
        router=router,
    )
    view = engine.build_view(DashboardState(), ReportBundle())
    assert view.valid is False
    assert any("ghost_widget" in w for w in view.warnings)
    assert "ghost_widget" not in view.widgets


def test_widget_exception_is_isolated_as_placeholder():
    class BoomWidget(BaseWidget):
        name = "boom"
        title = "Boom"

        def build(self, context):  # noqa: ANN001
            raise RuntimeError("kaputt")

    registry = WidgetRegistry()
    registry.register(BoomWidget())
    router = Router()
    router.register(PageLayout(Page.OVERVIEW, "Overview", "radar", {"center": ("boom",)}))
    engine = DashboardEngine(
        theme=load_theme(), settings=DashboardSettings(), registry=registry, router=router
    )
    view = engine.build_view(DashboardState(), ReportBundle())
    # Keine Exception nach außen: das Widget wird als Platzhalter dargestellt.
    spec = view.widgets["boom"]
    assert spec.placeholder is True
    assert spec.kind == KIND_TEXT
    assert any("boom" in w for w in view.warnings)


def test_engine_unchanged_for_new_page_via_router():
    # Neue Seite kommt nur über den Router; die Engine-Klasse bleibt unverändert.
    router = build_default_router()
    router.register(
        PageLayout(Page.OVERVIEW, "Custom Overview", "radar", {"center": ("settings_panel",)})
    )
    engine = DashboardEngine(
        theme=load_theme(),
        settings=DashboardSettings(),
        registry=build_default_registry(),
        router=router,
    )
    view = engine.build_view(DashboardState(active_page=Page.OVERVIEW), ReportBundle())
    assert view.title == "Custom Overview"
    assert "settings_panel" in view.widgets


def test_router_property_exposed():
    engine = _engine()
    assert isinstance(engine.router, Router)


def test_theme_property_exposed():
    engine = _engine()
    assert engine.theme is load_theme()


def test_view_regions_only_reference_present_widgets():
    engine = _engine()
    view = engine.build_view(DashboardState(active_page=Page.ANALYTICS), _full_bundle())
    for ids in view.regions.values():
        for widget_id in ids:
            assert widget_id in view.widgets


def test_analytics_page_has_eight_widgets():
    engine = _engine()
    view = engine.build_view(DashboardState(active_page=Page.ANALYTICS), _full_bundle())
    assert len(view.widgets) == 8
