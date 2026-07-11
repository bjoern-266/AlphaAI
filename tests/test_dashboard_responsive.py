"""Tests der Responsive-Anpassung (Umordnung, keine Fachlogik)."""

from __future__ import annotations

from dashboard.responsive import adapt_regions, column_count
from dashboard.state import DeviceClass

_REGIONS = {
    "left": ("a", "b"),
    "center": ("c",),
    "right": ("d",),
}


def test_column_count_desktop():
    assert column_count(DeviceClass.DESKTOP) == 3


def test_column_count_tablet():
    assert column_count(DeviceClass.TABLET) == 1


def test_column_count_ultrawide():
    assert column_count(DeviceClass.ULTRAWIDE) == 4


def test_column_count_uhd():
    assert column_count(DeviceClass.UHD_4K) == 4


def test_tablet_collapses_to_single_center():
    adapted = adapt_regions(dict(_REGIONS), DeviceClass.TABLET)
    assert set(adapted) == {"center"}
    assert adapted["center"] == ("a", "b", "c", "d")


def test_desktop_keeps_three_regions():
    adapted = adapt_regions(dict(_REGIONS), DeviceClass.DESKTOP)
    assert adapted["left"] == ("a", "b")
    assert adapted["center"] == ("c",)
    assert adapted["right"] == ("d",)


def test_ultrawide_keeps_regions():
    adapted = adapt_regions(dict(_REGIONS), DeviceClass.ULTRAWIDE)
    assert set(adapted) == {"left", "center", "right"}


def test_missing_region_defaults_to_empty():
    adapted = adapt_regions({"center": ("c",)}, DeviceClass.DESKTOP)
    assert adapted["left"] == ()
    assert adapted["right"] == ()


def test_tablet_preserves_order():
    regions = {"left": ("1",), "center": ("2", "3"), "right": ("4",)}
    adapted = adapt_regions(regions, DeviceClass.TABLET)
    assert adapted["center"] == ("1", "2", "3", "4")


def test_adapt_does_not_mutate_input():
    regions = {"left": ("a",), "center": ("b",), "right": ("c",)}
    adapt_regions(regions, DeviceClass.TABLET)
    assert regions == {"left": ("a",), "center": ("b",), "right": ("c",)}
