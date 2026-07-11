"""Tests der Dashboard-Anzeigeeinstellungen (nur Anzeige, keine Handelsparameter)."""

from __future__ import annotations

import pytest

from dashboard.settings import (
    DASHBOARD_SETTINGS_FILE,
    DashboardSettings,
    DashboardSettingsError,
    load_dashboard_settings,
    load_dashboard_settings_from_dict,
)


def test_defaults():
    settings = DashboardSettings()
    assert settings.default_page == "overview"
    assert settings.dark_mode is True
    assert settings.default_device == "desktop"
    assert settings.default_refresh_seconds == 0
    assert settings.refresh_options == (1, 5, 15, 30, 60)
    assert settings.table_page_size == 25


def test_load_from_dict_full():
    data = {
        "display": {
            "default_page": "analytics",
            "dark_mode": True,
            "default_device": "ultrawide",
            "sidebar_collapsed": True,
        },
        "refresh": {"default_seconds": 5, "options_seconds": [1, 5, 15, 30, 60]},
        "charts": {"default_type": "area", "show_grid": False, "animate": False},
        "tables": {"page_size": 50},
        "filters": {"default_direction": "long", "default_strength": "high"},
        "export": {"formats": ["csv", "png"]},
    }
    settings = load_dashboard_settings_from_dict(data)
    assert settings.default_page == "analytics"
    assert settings.default_device == "ultrawide"
    assert settings.sidebar_collapsed is True
    assert settings.default_refresh_seconds == 5
    assert settings.chart_default_type == "area"
    assert settings.chart_show_grid is False
    assert settings.table_page_size == 50
    assert settings.default_direction_filter == "long"
    assert settings.export_formats == ("csv", "png")


def test_load_from_dict_empty_uses_defaults():
    settings = load_dashboard_settings_from_dict({})
    assert settings.default_page == "overview"
    assert settings.refresh_options == (1, 5, 15, 30, 60)


def test_invalid_refresh_default_raises():
    data = {"refresh": {"default_seconds": 7, "options_seconds": [1, 5, 15]}}
    with pytest.raises(DashboardSettingsError):
        load_dashboard_settings_from_dict(data)


def test_refresh_manual_zero_is_valid_even_if_not_option():
    settings = load_dashboard_settings_from_dict(
        {"refresh": {"default_seconds": 0, "options_seconds": [5, 10]}}
    )
    assert settings.default_refresh_seconds == 0


def test_invalid_page_size_raises():
    with pytest.raises(DashboardSettingsError):
        load_dashboard_settings_from_dict({"tables": {"page_size": 0}})


def test_load_from_default_toml_file():
    settings = load_dashboard_settings()
    assert settings.default_page == "overview"
    assert settings.dark_mode is True
    assert settings.default_refresh_seconds == 0


def test_settings_file_exists():
    assert DASHBOARD_SETTINGS_FILE.is_file()


def test_missing_file_raises(tmp_path):
    with pytest.raises(DashboardSettingsError):
        load_dashboard_settings(tmp_path / "nope.toml")


def test_invalid_toml_raises(tmp_path):
    bad = tmp_path / "settings.toml"
    bad.write_text("this is = = not valid toml", encoding="utf-8")
    with pytest.raises(DashboardSettingsError):
        load_dashboard_settings(bad)


def test_settings_is_frozen():
    import dataclasses

    settings = DashboardSettings()
    with pytest.raises(dataclasses.FrozenInstanceError):
        settings.dark_mode = False  # type: ignore[misc]


def test_no_trading_parameters_in_settings():
    # Reine Anzeige: keine Handelsfelder wie capital/risk/leverage.
    field_names = {f.name for f in DashboardSettings.__dataclass_fields__.values()}
    for forbidden in ("capital", "risk", "leverage", "position_size", "stop_loss"):
        assert forbidden not in field_names
