"""Widgets der Live-Operations-Seite (nur Anzeige des OperationReport).

Diese Widgets **visualisieren ausschließlich** den bereits fertigen
OperationReport (über das View Model). Sie **berechnen nichts** und enthalten
**keine** Geschäfts-/Handelslogik – sie formatieren die vorhandenen Werte.
"""

from __future__ import annotations

from dashboard import format as fmt
from dashboard.widgets.base import BaseWidget, WidgetContext
from dashboard.widgets.common import card
from models.dashboard import (
    KIND_CARDS,
    KIND_LIST,
    KIND_STATUS,
    KIND_TABLE,
    TONE_ACCENT,
    TONE_DANGER,
    TONE_INFO,
    TONE_SUCCESS,
    TONE_WARNING,
    StatusItem,
    TableSpec,
    WidgetSpec,
)

_TOP_COLUMNS = ("#", "Ticker", "Sector", "Country", "Direction", "Score")
_JOB_COLUMNS = ("Job", "Typ", "Status", "Dauer", "Info")

_HEALTH_TONE = {"ok": TONE_SUCCESS, "degraded": TONE_WARNING, "error": TONE_DANGER}
_STATUS_TONE = {"success": TONE_SUCCESS, "failed": TONE_DANGER, "skipped": TONE_WARNING}


class MarketStatusWidget(BaseWidget):
    """Marktstatus Europa/USA mit Phase, offen/geschlossen und Countdown."""

    name = "lo_market_status"
    title = "Marktstatus"
    icon = "radar"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Markt-Status-Anzeige aus dem Live-Operations-View-Model."""
        vm = context.view_model.live_operations
        items = tuple(
            StatusItem(
                name=f"{market.title} ({market.phase})",
                status=(
                    f"offen · nächste Phase {market.next_phase} in "
                    f"{fmt.duration(market.seconds_to_next)}"
                    if market.is_open
                    else f"geschlossen · {market.next_phase} in "
                    f"{fmt.duration(market.seconds_to_next)}"
                ),
                tone=TONE_SUCCESS if market.is_open else TONE_INFO,
            )
            for market in vm.markets
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_STATUS,
            status_items=items,
            text=vm.current_session,
            icon=self.icon,
            placeholder=not items,
        )


class SystemStatusWidget(BaseWidget):
    """Systemstatus: Health, Heartbeat, laufender/nächster Job, Queue, Zähler."""

    name = "lo_system_status"
    title = "Systemstatus"
    icon = "signal"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die System-Kacheln aus dem Live-Operations-View-Model."""
        vm = context.view_model.live_operations
        health_tone = _HEALTH_TONE.get(vm.health or "", TONE_INFO)
        heartbeat = "lebendig" if vm.heartbeat_alive else "offline"
        cards = (
            card("Health", (vm.health or "—").upper(), health_tone),
            card("Heartbeat", heartbeat, TONE_SUCCESS if vm.heartbeat_alive else TONE_DANGER),
            card("Laufender Job", vm.running_job or "—", TONE_INFO),
            card("Queue", fmt.integer(vm.queue_size), TONE_INFO),
            card("Scans", fmt.integer(vm.scan_count), TONE_ACCENT),
            card(
                "Fehler", fmt.integer(vm.error_count), TONE_WARNING if vm.error_count else TONE_INFO
            ),
            card("Uptime", fmt.duration(vm.uptime_seconds), TONE_INFO),
            card("Ø Laufzeit", fmt.number(vm.average_runtime, 2), TONE_INFO),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=vm.health is None,
        )


class ScanScheduleWidget(BaseWidget):
    """Letzter Scan, nächster Scan und laufende Börsensitzung."""

    name = "lo_schedule"
    title = "Scans"
    icon = "target"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Scan-Übersicht aus dem Live-Operations-View-Model."""
        vm = context.view_model.live_operations
        cards = (
            card("Sitzung", vm.current_session or "—", TONE_ACCENT),
            card("Letzter Scan", fmt.clock_time(vm.last_scan_at), TONE_SUCCESS),
            card("Nächster Scan", fmt.clock_time(vm.next_scan_at), TONE_INFO),
            card("Nächster Job", vm.next_scan_job or "—", TONE_INFO),
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_CARDS,
            cards=cards,
            icon=self.icon,
            placeholder=vm.as_of is None,
        )


class TopOpportunitiesWidget(BaseWidget):
    """Top Opportunities des letzten automatischen Scans."""

    name = "lo_top_opportunities"
    title = "Top Opportunities"
    icon = "trending"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Top-Chancen-Tabelle aus dem letzten Discovery-Ergebnis."""
        rows = tuple(
            (
                str(row.rank),
                row.ticker or "—",
                row.sector or "—",
                row.country or "—",
                row.direction.upper(),
                fmt.number(row.score, 0),
            )
            for row in context.view_model.live_operations.top_rows
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_TOP_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )


class NewSignalsWidget(BaseWidget):
    """Neue Chancen und neue Risiken seit dem letzten Scan."""

    name = "lo_new_signals"
    title = "Neu seit letztem Scan"
    icon = "activity"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Liste neuer Chancen/Risiken aus dem View-Model."""
        vm = context.view_model.live_operations
        items = tuple(f"✚ {ticker}" for ticker in vm.new_opportunities) + tuple(
            f"⚠ {ticker}" for ticker in vm.new_risks
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_LIST,
            items=items,
            icon=self.icon,
            placeholder=not items,
        )


class JobHistoryWidget(BaseWidget):
    """Verlauf der zuletzt gelaufenen Jobs."""

    name = "lo_job_history"
    title = "Job Historie"
    icon = "database"

    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Job-Historie-Tabelle aus dem View-Model."""
        rows = tuple(
            (
                job.name,
                job.job_type,
                job.status.upper(),
                fmt.number(job.duration_seconds, 2),
                job.error or job.summary or "—",
            )
            for job in context.view_model.live_operations.jobs
        )
        return WidgetSpec(
            widget_id=self.name,
            title=self.title,
            kind=KIND_TABLE,
            table=TableSpec(columns=_JOB_COLUMNS, rows=rows),
            icon=self.icon,
            placeholder=not rows,
        )
