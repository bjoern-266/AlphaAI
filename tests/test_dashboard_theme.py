"""Tests des Dashboard-Themes (die einzige Quelle des Aussehens)."""

from __future__ import annotations

import dataclasses

import pytest

from dashboard.theme import (
    DEFAULT_THEME,
    Animation,
    Borders,
    Palette,
    Spacing,
    Theme,
    Typography,
    load_theme,
)
from models.dashboard import (
    TONE_ACCENT,
    TONE_DANGER,
    TONE_INFO,
    TONE_NEUTRAL,
    TONE_SUCCESS,
    TONE_WARNING,
)


def test_palette_exact_colors():
    p = Palette()
    assert p.primary_background == "#090909"
    assert p.secondary_background == "#111111"
    assert p.carbon_surface == "#171717"
    assert p.card == "#1F1F1F"
    assert p.border == "#2E2E2E"
    assert p.carbon_highlight == "#343434"
    assert p.primary_accent == "#F2C94C"
    assert p.hover_accent == "#FFD54F"
    assert p.success == "#27AE60"
    assert p.warning == "#F2994A"
    assert p.danger == "#EB5757"
    assert p.information == "#56CCF2"
    assert p.text == "#F5F5F5"
    assert p.secondary_text == "#A8A8A8"


def test_typography_fonts():
    t = Typography()
    assert t.primary == "Inter"
    assert t.monospace == "JetBrains Mono"
    assert t.alternate == "IBM Plex Sans"


def test_spacing_scale_monotonic():
    s = Spacing()
    assert s.xs < s.sm < s.md < s.lg < s.xl < s.xxl


def test_borders_defaults():
    b = Borders()
    assert b.color == "#2E2E2E"
    assert b.highlight_color == "#343434"
    assert b.radius_sm_px < b.radius_md_px < b.radius_lg_px


def test_animation_timings():
    a = Animation()
    assert a.fast_ms < a.base_ms < a.slow_ms
    assert "cubic-bezier" in a.easing


def test_chart_palette_only_allowed_colors():
    theme = Theme()
    assert theme.chart_palette == ("#F2C94C", "#27AE60", "#EB5757", "#56CCF2", "#A8A8A8")


def test_color_for_tone_maps_all_tones():
    theme = Theme()
    assert theme.color_for_tone(TONE_SUCCESS) == "#27AE60"
    assert theme.color_for_tone(TONE_DANGER) == "#EB5757"
    assert theme.color_for_tone(TONE_WARNING) == "#F2994A"
    assert theme.color_for_tone(TONE_INFO) == "#56CCF2"
    assert theme.color_for_tone(TONE_ACCENT) == "#F2C94C"
    assert theme.color_for_tone(TONE_NEUTRAL) == "#F5F5F5"


def test_color_for_tone_unknown_falls_back_to_text():
    theme = Theme()
    assert theme.color_for_tone("does-not-exist") == theme.palette.text


def test_icon_lookup_known_and_unknown():
    theme = Theme()
    assert theme.icon("overview") == "radar"
    assert theme.icon("analytics") == "trending"
    assert theme.icon("unknown-icon") == "unknown-icon"


def test_icons_cover_nine_pages():
    theme = Theme()
    for page in (
        "overview",
        "live_analysis",
        "paper_portfolio",
        "backtesting",
        "analytics",
        "performance",
        "trade_journal",
        "recommendations",
        "settings",
    ):
        assert page in theme.icons


def test_font_stack_contains_families():
    theme = Theme()
    stack = theme.font_stack()
    assert "Inter" in stack
    assert "IBM Plex Sans" in stack


def test_materials_present():
    theme = Theme()
    for name in (
        "dark_carbon",
        "brushed_metal",
        "matt_black",
        "tinted_glass",
        "soft_glow",
        "subtle_reflection",
    ):
        assert name in theme.materials


def test_theme_is_frozen():
    theme = Theme()
    with pytest.raises(dataclasses.FrozenInstanceError):
        theme.chart_palette = ()  # type: ignore[misc]


def test_load_theme_returns_default_singleton():
    assert load_theme() is DEFAULT_THEME


def test_default_theme_dark_background():
    # Dark-Carbon-Designziel: sehr dunkler Primärhintergrund.
    assert DEFAULT_THEME.palette.primary_background == "#090909"
