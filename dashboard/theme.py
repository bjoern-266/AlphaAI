"""Theme des AlphaAI Command Center – **die einzige** Quelle des Aussehens.

Sämtliche Farben, Schriften, Abstände, Rahmen, Radien, Animationen, Materialien
und Icon-Namen liegen ausschließlich hier. Im übrigen Dashboard-Code gibt es
**keine** hartcodierten Gestaltungswerte – Widgets und Charts beziehen alle
visuellen Größen aus dem :class:`Theme`.

Designziel: „Dark Carbon", industriell, hochwertig, minimalistisch, futuristisch
– die Atmosphäre eines professionellen Trading-Intelligence-Command-Centers
(keine Logos, keine Namen, keine geschützten Elemente). ~90 % Schwarz/Grau,
~10 % gelbe Akzente.

Alle Theme-Typen sind unveränderlich (`frozen`); es findet keine Berechnung und
keine Fachlogik statt.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.dashboard import (
    TONE_ACCENT,
    TONE_DANGER,
    TONE_INFO,
    TONE_NEUTRAL,
    TONE_SUCCESS,
    TONE_WARNING,
)


@dataclass(frozen=True, slots=True)
class Palette:
    """Farbpalette (Dark Carbon)."""

    primary_background: str = "#090909"
    secondary_background: str = "#111111"
    carbon_surface: str = "#171717"
    card: str = "#1F1F1F"
    border: str = "#2E2E2E"
    carbon_highlight: str = "#343434"
    primary_accent: str = "#F2C94C"
    hover_accent: str = "#FFD54F"
    success: str = "#27AE60"
    warning: str = "#F2994A"
    danger: str = "#EB5757"
    information: str = "#56CCF2"
    text: str = "#F5F5F5"
    secondary_text: str = "#A8A8A8"


@dataclass(frozen=True, slots=True)
class Typography:
    """Schriftfamilien (Anzeige, Monospace, Alternative)."""

    primary: str = "Inter"
    monospace: str = "JetBrains Mono"
    alternate: str = "IBM Plex Sans"
    base_size_px: int = 14
    heading_size_px: int = 20
    mono_size_px: int = 13


@dataclass(frozen=True, slots=True)
class Spacing:
    """Abstands-Skala in Pixeln."""

    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 24
    xxl: int = 32


@dataclass(frozen=True, slots=True)
class Borders:
    """Rahmen- und Radius-Einstellungen."""

    width_px: int = 1
    color: str = "#2E2E2E"
    highlight_color: str = "#343434"
    radius_sm_px: int = 6
    radius_md_px: int = 10
    radius_lg_px: int = 16


@dataclass(frozen=True, slots=True)
class Animation:
    """Animations-Timings (nur Anzeige)."""

    fast_ms: int = 120
    base_ms: int = 200
    slow_ms: int = 400
    easing: str = "cubic-bezier(0.4, 0.0, 0.2, 1)"
    fade_ms: int = 250


@dataclass(frozen=True, slots=True)
class Theme:
    """Gebündeltes Theme (unveränderlich).

    Attributes:
        palette: Farbpalette.
        typography: Schriften.
        spacing: Abstände.
        borders: Rahmen/Radien.
        animation: Animations-Timings.
        icons: Zuordnung semantischer Name → Icon-Name (Outline-Stil).
        materials: Materialbeschreibungen (Dark Carbon, Brushed Metal, …).
        chart_palette: Reihenfolge der Chart-Datenfarben (Gold/Grün/Rot/Cyan …).
    """

    palette: Palette = field(default_factory=Palette)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    borders: Borders = field(default_factory=Borders)
    animation: Animation = field(default_factory=Animation)
    icons: dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_ICONS))
    materials: dict[str, str] = field(default_factory=lambda: dict(_DEFAULT_MATERIALS))
    chart_palette: tuple[str, ...] = (
        "#F2C94C",  # Gold
        "#27AE60",  # Grün
        "#EB5757",  # Rot
        "#56CCF2",  # Cyan
        "#A8A8A8",  # Grau (neutral)
    )

    def color_for_tone(self, tone: str) -> str:
        """Löst eine semantische Tönung in eine Farbe auf."""
        return _TONE_COLORS.get(tone, self.palette.text) or self.palette.text

    def icon(self, name: str) -> str:
        """Gibt den Icon-Namen zu einem semantischen Schlüssel zurück."""
        return self.icons.get(name, name)

    def font_stack(self) -> str:
        """CSS-Fontstack aus den drei Schriftfamilien (Fallback-Kette)."""
        t = self.typography
        return f'"{t.primary}", "{t.alternate}", sans-serif'


# Icon-Namen (Outline-Stil). Werte sind bewusst neutrale, generische Namen.
_DEFAULT_ICONS: dict[str, str] = {
    "overview": "radar",
    "live_analysis": "activity",
    "paper_portfolio": "layers",
    "backtesting": "database",
    "analytics": "trending",
    "performance": "signal",
    "trade_journal": "target",
    "recommendations": "signal",
    "market_intelligence": "radar",
    "market_discovery": "database",
    "settings": "shield",
    "risk": "shield",
    "radar": "radar",
    "shield": "shield",
    "activity": "activity",
    "target": "target",
    "layers": "layers",
    "database": "database",
    "signal": "signal",
    "trending": "trending",
}

# Materialbeschreibungen (nur Anzeige, kein Verhalten).
_DEFAULT_MATERIALS: dict[str, str] = {
    "dark_carbon": "linear-gradient(145deg, #111111, #090909)",
    "brushed_metal": (
        "repeating-linear-gradient(135deg, #1F1F1F, #1F1F1F 2px, #171717 2px, #171717 4px)"
    ),
    "matt_black": "#090909",
    "tinted_glass": "rgba(31, 31, 31, 0.72)",
    "soft_glow": "0 0 24px rgba(242, 201, 76, 0.12)",
    "subtle_reflection": "inset 0 1px 0 rgba(255, 255, 255, 0.04)",
}

# Zuordnung Tönung → Farbe (aus der Standardpalette abgeleitet, einmalig).
_DEFAULT_PALETTE = Palette()
_TONE_COLORS: dict[str, str] = {
    TONE_NEUTRAL: _DEFAULT_PALETTE.text,
    TONE_SUCCESS: _DEFAULT_PALETTE.success,
    TONE_DANGER: _DEFAULT_PALETTE.danger,
    TONE_WARNING: _DEFAULT_PALETTE.warning,
    TONE_INFO: _DEFAULT_PALETTE.information,
    TONE_ACCENT: _DEFAULT_PALETTE.primary_accent,
}

# Das Standard-Theme. Ein Aufrufer erhält immer dieselbe, unveränderliche Instanz.
DEFAULT_THEME = Theme()


def load_theme() -> Theme:
    """Gibt das Standard-Theme zurück (Gestaltung liegt vollständig hier)."""
    return DEFAULT_THEME
