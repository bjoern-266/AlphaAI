"""Tests der Operations Engine (Regel-Laden, Tick, Report, Validierung)."""

from __future__ import annotations

import copy
from datetime import UTC, datetime, timedelta

import pytest

from engines.operations_engine import (
    OperationsEngine,
    OperationsRulesError,
    load_operations_rules,
    load_operations_rules_from_dict,
)
from models.market_discovery import DiscoveryReport
from models.operations import JobStatus, OperationReport, SystemHealth
from tests.operations_helpers import (
    RULES_DICT,
    default_jobs,
    make_discovery_report,
    make_engine,
    make_rules,
    rules_dict,
)

# --- Regel-Laden ----------------------------------------------------------- #


def test_load_from_default_file():
    rules = load_operations_rules()
    assert rules.version >= 1
    assert len(rules.sessions) >= 2
    assert len(rules.schedule) >= 1


def test_load_from_dict():
    rules = make_rules()
    assert rules.version == 1
    assert {s.key for s in rules.sessions} == {"europe", "us"}
    assert len(rules.schedule) == 3


def test_missing_markets_raises():
    data = copy.deepcopy(RULES_DICT)
    del data["markets"]
    with pytest.raises(OperationsRulesError):
        load_operations_rules_from_dict(data)


def test_invalid_timezone_raises():
    data = rules_dict()
    data["markets"]["europe"]["timezone"] = "Mars/Base"
    with pytest.raises(OperationsRulesError):
        load_operations_rules_from_dict(data)


def test_invalid_market_time_raises():
    data = rules_dict()
    data["markets"]["europe"]["phases"][0][1] = "99:99"
    with pytest.raises(OperationsRulesError):
        load_operations_rules_from_dict(data)


def test_duplicate_job_names_raises():
    data = rules_dict()
    data["schedule"].append(
        {"name": "europe_open", "job_type": "analytics", "time": "10:00", "timezone": "UTC"}
    )
    with pytest.raises(OperationsRulesError):
        load_operations_rules_from_dict(data)


def test_bad_schedule_type_raises():
    data = rules_dict()
    data["schedule"] = "not-a-list"
    with pytest.raises(OperationsRulesError):
        load_operations_rules_from_dict(data)


def test_missing_file_raises(tmp_path):
    with pytest.raises(OperationsRulesError):
        load_operations_rules(tmp_path / "nope.toml")


# --- build_report ---------------------------------------------------------- #


def test_build_report_market_clock():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.build_report()
    assert isinstance(report, OperationReport)
    assert "us" in report.market_clock.open_markets  # Opening Bell


def test_build_report_next_scan():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 3, 0, tzinfo=UTC))
    report = engine.build_report()
    assert report.next_scan_at is not None
    assert report.next_scan_job != ""


def test_build_report_current_session_closed():
    # 03:00 UTC: Europa (05:00 Berlin) und US (23:00 Vortag) geschlossen.
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 3, 0, tzinfo=UTC))
    report = engine.build_report()
    assert report.current_session == "Alle Märkte geschlossen"


def test_build_report_current_session_open():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.build_report()
    assert "USA" in report.current_session


# --- tick / Jobs ----------------------------------------------------------- #


def test_tick_runs_due_jobs():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.tick()
    assert report.scan_count >= 1
    assert report.discovery is not None


def test_tick_sets_heartbeat_alive():
    engine, _ = make_engine()
    report = engine.tick()
    assert report.system_state.heartbeat.alive is True


def test_tick_updates_discovery_new_opportunities():
    engine, holder = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.tick()
    assert report.new_opportunities == ("AAPL", "NVDA")


def test_second_day_detects_new_ticker():
    calls = {"n": 0}

    def discovery():
        calls["n"] += 1
        return make_discovery_report(("AAPL",) if calls["n"] == 1 else ("AAPL", "TSLA"))

    jobs = {**default_jobs(), "discovery": discovery}
    engine, holder = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs=jobs)
    engine.tick()
    holder["now"] = holder["now"] + timedelta(days=1)
    report = engine.tick()
    assert "TSLA" in report.new_opportunities


def test_new_risks_detected():
    def discovery():
        return make_discovery_report(("AAPL", "RISKY"), risky=("RISKY",))

    jobs = {**default_jobs(), "discovery": discovery}
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs=jobs)
    report = engine.tick()
    assert "RISKY" in report.new_risks


def test_job_crash_does_not_block_scheduler():
    def boom():
        raise RuntimeError("kaputt")

    jobs = {**default_jobs(), "discovery": boom}
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs=jobs)
    report = engine.tick()
    # Der Fehler wird gezählt, der Scheduler läuft weiter (analytics lief).
    assert report.error_count >= 1
    assert any(run.status is JobStatus.FAILED for run in report.job_history)


def test_missing_job_function_skips():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs={})
    report = engine.tick()
    assert any(run.status is JobStatus.SKIPPED for run in report.job_history)


def test_job_not_repeated_once_drained():
    # Mehrere Jobs sind fällig; die Exklusivität verteilt Discovery über Ticks
    # (automatische Wiederaufnahme). Sind alle abgearbeitet, kommt nichts hinzu.
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    for _ in range(4):
        engine.tick()
    stable = engine.build_report().scan_count
    engine.tick()
    assert engine.build_report().scan_count == stable


def test_only_one_discovery_per_tick():
    # Beide Discovery-Jobs (europe_open, us_open) sind um 13:35 UTC fällig,
    # aber nur eines läuft pro Tick (Exklusivität).
    runs = {"n": 0}

    def discovery():
        runs["n"] += 1
        return make_discovery_report()

    jobs = {**default_jobs(), "discovery": discovery}
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs=jobs)
    engine.tick()
    assert runs["n"] == 1


def test_error_count_and_health_degraded():
    def boom():
        raise RuntimeError("x")

    jobs = {"discovery": boom, "analytics": boom, "market_intelligence": boom}
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC), jobs=jobs)
    report = engine.tick()
    assert report.error_count >= 1
    assert report.system_state.health in {SystemHealth.DEGRADED, SystemHealth.ERROR}


def test_last_successful_scan_recorded():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.tick()
    assert report.last_successful_scan_at is not None


def test_uptime_recorded():
    engine, holder = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    engine.tick()
    holder["now"] = holder["now"] + timedelta(seconds=120)
    report = engine.build_report()
    assert report.system_state.uptime_seconds == 120


def test_from_config_builds_engine():
    engine = OperationsEngine.from_config(jobs=default_jobs())
    report = engine.build_report()
    assert isinstance(report, OperationReport)


def test_registry_property():
    engine, _ = make_engine()
    assert "discovery" in engine.registry


def test_discovery_result_is_discovery_report():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.tick()
    assert isinstance(report.discovery, DiscoveryReport)


def test_average_runtime_present_after_run():
    engine, _ = make_engine(clock_time=datetime(2024, 6, 3, 13, 35, tzinfo=UTC))
    report = engine.tick()
    assert report.average_runtime is not None


def test_metadata_version():
    engine, _ = make_engine()
    assert engine.build_report().metadata["rules_version"] == 1


def test_beat_initializes_uptime():
    engine, holder = make_engine()
    engine.beat()
    holder["now"] = holder["now"] + timedelta(seconds=30)
    assert engine.build_report().system_state.uptime_seconds == 30
