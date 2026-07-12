"""Tests des Routers (neue Seiten nur hier; Engine bleibt unverändert)."""

from __future__ import annotations

import dataclasses

import pytest

from dashboard.router import (
    KEYBOARD_SHORTCUTS,
    REGIONS,
    NavItem,
    PageLayout,
    Router,
    build_default_router,
)
from dashboard.state import Page
from dashboard.widget_registry import build_default_registry


def test_default_router_has_all_pages():
    router = build_default_router()
    assert len(router.pages()) == 11
    for page in Page:
        assert router.has(page)


def test_resolve_returns_layout_with_title():
    router = build_default_router()
    layout = router.resolve(Page.OVERVIEW)
    assert layout.title == "Overview"
    assert layout.page is Page.OVERVIEW


def test_resolve_unknown_page_fallback():
    router = Router()
    layout = router.resolve(Page.ANALYTICS)
    assert layout.page is Page.ANALYTICS
    assert layout.regions == {}


def test_layout_regions_use_known_keys():
    router = build_default_router()
    for page in Page:
        layout = router.resolve(page)
        for region in layout.regions:
            assert region in REGIONS


def test_all_layout_widget_ids_are_registered():
    router = build_default_router()
    registry = build_default_registry()
    for page in Page:
        for widget_id in router.resolve(page).widget_ids():
            assert widget_id in registry, f"{widget_id} fehlt in der Registry"


def test_widget_ids_ordered_left_center_right():
    layout = PageLayout(
        page=Page.OVERVIEW,
        title="Overview",
        icon="radar",
        regions={"right": ("c",), "left": ("a",), "center": ("b",)},
    )
    assert layout.widget_ids() == ("a", "b", "c")


def test_nav_items_count():
    router = build_default_router()
    items = router.nav_items()
    assert len(items) == 11
    assert all(isinstance(item, NavItem) for item in items)


def test_nav_items_use_icon_overrides():
    router = build_default_router()
    items = router.nav_items({"overview": "custom-radar"})
    overview = next(item for item in items if item.page is Page.OVERVIEW)
    assert overview.icon == "custom-radar"


def test_register_overrides_layout():
    router = Router()
    router.register(PageLayout(Page.OVERVIEW, "First", "radar", {}))
    router.register(PageLayout(Page.OVERVIEW, "Second", "radar", {}))
    assert router.resolve(Page.OVERVIEW).title == "Second"
    assert len(router.pages()) == 1


def test_keyboard_shortcuts_navigation():
    assert KEYBOARD_SHORTCUTS["F5"] == "refresh"
    assert KEYBOARD_SHORTCUTS["Ctrl+1"] == Page.OVERVIEW.value
    assert KEYBOARD_SHORTCUTS["Ctrl+2"] == Page.ANALYTICS.value
    assert KEYBOARD_SHORTCUTS["Ctrl+3"] == Page.PAPER_PORTFOLIO.value
    assert KEYBOARD_SHORTCUTS["Ctrl+4"] == Page.BACKTESTING.value
    assert KEYBOARD_SHORTCUTS["Ctrl+5"] == Page.TRADE_JOURNAL.value


def test_page_layout_is_frozen():
    layout = PageLayout(Page.OVERVIEW, "Overview", "radar", {})
    with pytest.raises(dataclasses.FrozenInstanceError):
        layout.title = "x"  # type: ignore[misc]


def test_overview_layout_has_three_regions():
    layout = build_default_router().resolve(Page.OVERVIEW)
    assert set(layout.regions) == {"left", "center", "right"}


def test_settings_layout_center_only():
    layout = build_default_router().resolve(Page.SETTINGS)
    assert "settings_panel" in layout.widget_ids()
