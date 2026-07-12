"""End-to-End-Szenarien der Live Operations Platform (Börsentag).

Prüft, dass AlphaAI ohne Benutzereingriff automatisch arbeitet: Europa wird
morgens analysiert, vor der US-Öffnung erfolgt eine Vorbereitung, nach der
Öffnung eine vollständige Analyse, und das Dashboard-Report zeigt jederzeit
Marktstatus und die besten Chancen. Es werden **niemals** Orders ausgeführt.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from engines.operations_engine import OperationsEngine
from models.operations import JobStatus
from tests.operations_helpers import default_jobs, make_discovery_report, make_rules


def _engine():
    holder = {"now": datetime(2024, 6, 3, 5, 0, tzinfo=UTC)}  # 07:00 Berlin (vor Handel)
    calls = {"discovery": 0, "analytics": 0}

    def discovery():
        calls["discovery"] += 1
        # Wachsende Kandidatenliste über den Tag.
        return make_discovery_report(("AAPL", "NVDA", "MSFT")[: calls["discovery"] + 1])

    def analytics():
        calls["analytics"] += 1
        return "analytics"

    jobs = {**default_jobs(), "discovery": discovery, "analytics": analytics}
    engine = OperationsEngine(rules=make_rules(), jobs=jobs, clock=lambda: holder["now"])
    return engine, holder, calls


def _advance(engine, holder, to_hour_utc):
    holder["now"] = holder["now"].replace(hour=to_hour_utc, minute=35)
    return engine.tick()


def test_starts_without_user_input():
    engine, holder, _ = _engine()
    # Ohne Eingaben liefert der erste Tick sofort einen belastbaren Report.
    report = engine.tick()
    assert report.valid is True
    assert report.market_clock is not None


def test_europe_analyzed_automatically():
    engine, holder, calls = _engine()
    holder["now"] = datetime(2024, 6, 3, 7, 5, tzinfo=UTC)  # 09:05 Berlin (Öffnung)
    report = engine.tick()
    assert calls["discovery"] >= 1  # Europa-Discovery lief automatisch
    assert "europe" in report.market_clock.open_markets


def test_us_preparation_before_open():
    engine, holder, calls = _engine()
    holder["now"] = datetime(2024, 6, 3, 13, 5, tzinfo=UTC)  # 09:05 NY (pre-market)
    report = engine.tick()
    us = report.market_clock.get("us")
    assert us.is_open is False  # noch nicht geöffnet
    # Vorbereitung (Discovery) ist gelaufen.
    assert report.scan_count >= 1


def test_full_analysis_after_us_open():
    engine, holder, calls = _engine()
    holder["now"] = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)  # 09:35 NY (Opening Bell)
    report = engine.tick()
    assert report.market_clock.get("us").is_open is True
    assert report.discovery is not None
    assert report.discovery.opportunity_count >= 1


def test_dashboard_report_has_market_status_and_opportunities():
    engine, holder, _ = _engine()
    report = _advance(engine, holder, 13)
    # Marktstatus + Top Opportunities jederzeit verfügbar.
    assert report.market_clock.markets
    assert report.discovery is not None
    assert report.next_scan_at is not None


def test_no_orders_ever_executed():
    engine, holder, _ = _engine()
    report = engine.tick()
    # Es gibt keinerlei Order-Felder – das System führt nie Orders aus.
    assert not hasattr(report, "orders")
    assert not hasattr(report, "executed_trades")


def test_scans_accumulate_over_day():
    engine, holder, _ = _engine()
    engine.tick()
    first = engine.build_report().scan_count
    holder["now"] = holder["now"] + timedelta(hours=9)  # später am Tag
    engine.tick()
    assert engine.build_report().scan_count >= first


def test_new_opportunities_tracked_across_scans():
    engine, holder, _ = _engine()
    holder["now"] = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    report = engine.tick()
    assert report.new_opportunities  # erste Chancen sind „neu"


def test_health_ok_on_clean_day():
    engine, holder, _ = _engine()
    report = engine.tick()
    assert report.system_state.health.value == "ok"


def test_heartbeat_alive_on_tick():
    engine, holder, _ = _engine()
    report = engine.tick()
    assert report.system_state.heartbeat.alive is True


def test_job_history_records_runs():
    engine, holder, _ = _engine()
    holder["now"] = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    report = engine.tick()
    assert len(report.job_history) >= 1
    assert any(run.status is JobStatus.SUCCESS for run in report.job_history)


def test_next_scan_countdown_available():
    engine, holder, _ = _engine()
    report = engine.build_report()
    assert report.next_scan_job != ""
    assert report.next_scan_at is not None


def test_current_session_describes_open_markets():
    engine, holder, _ = _engine()
    report = _advance(engine, holder, 13)  # US offen
    assert "USA" in report.current_session


def test_daily_resumption_next_day():
    engine, holder, _ = _engine()
    holder["now"] = datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    engine.tick()
    for _ in range(3):
        engine.tick()
    day1 = engine.build_report().scan_count
    holder["now"] = holder["now"] + timedelta(days=1)
    engine.tick()
    assert engine.build_report().scan_count > day1


def test_report_is_ui_independent():
    # Der Report enthält nur Daten (keine UI-/Streamlit-Abhängigkeiten) und kann
    # so vom Desktop-Dashboard und späteren REST-/Mobile-Clients genutzt werden.
    engine, holder, _ = _engine()
    report = engine.tick()
    import dataclasses

    assert dataclasses.is_dataclass(report)
