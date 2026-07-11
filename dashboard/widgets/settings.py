"""Widget der Settings-Seite – **nur Anzeigeoptionen** (keine Handelsparameter)."""

from __future__ import annotations

from dashboard.widgets.base import BaseWidget, WidgetContext
from models.dashboard import KIND_CARDS, TONE_INFO, TONE_NEUTRAL, MetricCard, WidgetSpec


class SettingsWidget(BaseWidget):
    """Zeigt die aktuellen Anzeigeeinstellungen (Dark Mode, Refresh, Charts, …)."""

    name = "settings_panel"
    title = "Display Settings"
    icon = "shield"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Anzeige der Einstellungen (rein informativ, keine Fachparameter)."""
        settings = context.settings
        state = context.state
        cards = (
            MetricCard("Dark Mode", "ON" if settings.dark_mode else "OFF", tone=TONE_INFO),
            MetricCard("Refresh Rate", f"{state.refresh_rate.value} s", tone=TONE_INFO),
            MetricCard("Device", state.device_class.value, tone=TONE_NEUTRAL),
            MetricCard("Default Chart", settings.chart_default_type, tone=TONE_NEUTRAL),
            MetricCard("Table Page Size", str(settings.table_page_size), tone=TONE_NEUTRAL),
            MetricCard("Export", ", ".join(settings.export_formats), tone=TONE_NEUTRAL),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            text="Nur Anzeigeoptionen – keine Handelsparameter.",
        )
