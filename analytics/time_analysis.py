"""Time Analysis – zeitliche Kennzahlen.

Gruppiert die Trades nach Wochentag, Monat, Handelsstunde und Haltedauer-Bereich
(anhand des Einstiegs-Zeitstempels bzw. der Haltedauer) und berechnet je Gruppe
die Kennzahlen. Reine Auswertung, keine Bewertung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from analytics import aggregation as agg
from analytics.base import AnalyticsContext, AnalyticsModelOutput, BaseAnalyticsModel
from analytics.labeling import UNKNOWN, holding_band
from models.analytics import AnalyticsTrade

_WEEKDAYS = ("Mo", "Di", "Mi", "Do", "Fr", "Sa", "So")


def _weekday(trade: AnalyticsTrade) -> str:
    """Wochentag des Einstiegs (Kürzel) oder ``"unbekannt"``."""
    return _WEEKDAYS[trade.entry_time.weekday()] if trade.entry_time else UNKNOWN


def _month(trade: AnalyticsTrade) -> str:
    """Monat des Einstiegs (``01``..``12``) oder ``"unbekannt"``."""
    return f"{trade.entry_time.month:02d}" if trade.entry_time else UNKNOWN


def _hour(trade: AnalyticsTrade) -> str:
    """Handelsstunde des Einstiegs (``00``..``23``) oder ``"unbekannt"``."""
    return f"{trade.entry_time.hour:02d}" if trade.entry_time else UNKNOWN


class TimeAnalysisModel(BaseAnalyticsModel):
    """Berechnet zeitliche Kennzahlen (Wochentag/Monat/Stunde/Haltedauer)."""

    name = "time_analysis"
    value_range = "Kennzahlen je Zeitdimension"

    def compute(self, context: AnalyticsContext, params: Mapping[str, Any]) -> AnalyticsModelOutput:
        """Gruppiert nach Wochentag, Monat, Stunde und Haltedauer-Bereich."""
        base_capital = float(context.config.get("base_capital", agg.DEFAULT_BASE_CAPITAL))
        bands = [float(b) for b in context.config.get("holding_bands", [1, 3, 7])]
        trades = context.trades

        statistics = {
            "weekday": agg.grouped_statistics(trades, _weekday, base_capital),
            "month": agg.grouped_statistics(trades, _month, base_capital),
            "hour": agg.grouped_statistics(trades, _hour, base_capital),
            "holding": agg.grouped_statistics(
                trades, lambda t: holding_band(t.holding_days, bands), base_capital
            ),
        }
        return AnalyticsModelOutput(
            name=self.name,
            statistics=statistics,
            metrics={"weekday_count": float(len(statistics["weekday"]))},
            reasons=["Zeitliche Kennzahlen (Wochentag/Monat/Stunde/Haltedauer) ausgewertet."],
        )
