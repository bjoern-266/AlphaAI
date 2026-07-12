"""Tests des aggregierten Health-Monitors (Sprint 17)."""

from __future__ import annotations

from application.health import HealthMonitor
from application.repositories import ReportStore
from models.application import HealthStatus, ReportKind
from tests.application_helpers import make_store, operations_payload


def _monitor(store: ReportStore, **kwargs) -> HealthMonitor:
    return HealthMonitor(store, version="1.0.0", **kwargs)


def test_report_has_all_components() -> None:
    report = _monitor(make_store()).report()
    names = {c.name for c in report.components}
    assert names == {"api", "persistence", "scheduler", "market", "queue", "cache", "system"}


def test_api_component_ok() -> None:
    report = _monitor(make_store()).report()
    assert report.component("api").status is HealthStatus.OK


def test_persistence_ok_with_reports() -> None:
    report = _monitor(make_store()).report()
    assert report.component("persistence").status is HealthStatus.OK


def test_persistence_degraded_when_empty() -> None:
    report = _monitor(make_store(populate=False)).report()
    assert report.component("persistence").status is HealthStatus.DEGRADED


def test_scheduler_unknown_without_operations() -> None:
    report = _monitor(make_store(populate=False)).report()
    assert report.component("scheduler").status is HealthStatus.UNKNOWN


def test_scheduler_ok_with_heartbeat() -> None:
    report = _monitor(make_store()).report()
    assert report.component("scheduler").status is HealthStatus.OK


def test_scheduler_degraded_when_heartbeat_dead() -> None:
    store = make_store(populate=False)
    payload = operations_payload()
    payload["system_state"]["heartbeat"]["alive"] = False
    store.save(ReportKind.OPERATIONS.value, payload)
    report = _monitor(store).report()
    assert report.component("scheduler").status is HealthStatus.DEGRADED


def test_market_ok_with_markets() -> None:
    report = _monitor(make_store()).report()
    market = report.component("market")
    assert market.status is HealthStatus.OK
    assert market.metrics["markets"] == 2


def test_market_degraded_without_markets() -> None:
    store = make_store(populate=False)
    payload = operations_payload()
    payload["market_clock"]["markets"] = []
    store.save(ReportKind.OPERATIONS.value, payload)
    report = _monitor(store).report()
    assert report.component("market").status is HealthStatus.DEGRADED


def test_queue_reports_size() -> None:
    report = _monitor(make_store()).report()
    assert report.component("queue").metrics["queue_size"] == 0


def test_cache_unknown_without_metrics() -> None:
    report = _monitor(make_store()).report()
    assert report.component("cache").status is HealthStatus.UNKNOWN


def test_cache_ok_with_metrics() -> None:
    report = _monitor(make_store(), cache_metrics=lambda: {"hits": 3, "misses": 1}).report()
    cache = report.component("cache")
    assert cache.status is HealthStatus.OK
    assert cache.metrics["hits"] == 3


def test_cache_error_when_metrics_raise() -> None:
    def boom() -> dict:
        raise RuntimeError("kaputt")

    report = _monitor(make_store(), cache_metrics=boom).report()
    assert report.component("cache").status is HealthStatus.ERROR


def test_system_ok() -> None:
    report = _monitor(make_store()).report()
    assert report.component("system").status is HealthStatus.OK


def test_system_error_maps() -> None:
    store = make_store(populate=False)
    payload = operations_payload()
    payload["system_state"]["health"] = "error"
    store.save(ReportKind.OPERATIONS.value, payload)
    report = _monitor(store).report()
    assert report.component("system").status is HealthStatus.ERROR


def test_overall_ok_when_all_ok() -> None:
    report = _monitor(make_store(), cache_metrics=lambda: {"hits": 0}).report()
    assert report.status is HealthStatus.OK
    assert report.healthy is True


def test_overall_is_worst_component() -> None:
    store = make_store(populate=False)
    payload = operations_payload()
    payload["system_state"]["health"] = "error"
    store.save(ReportKind.OPERATIONS.value, payload)
    report = _monitor(store, cache_metrics=lambda: {"hits": 0}).report()
    assert report.status is HealthStatus.ERROR


def test_overall_unknown_without_cache_and_operations() -> None:
    report = _monitor(make_store(populate=False)).report()
    # Persistence degraded + several unknown ⇒ mindestens DEGRADED.
    assert report.status in {HealthStatus.DEGRADED, HealthStatus.UNKNOWN}


def test_report_version_field() -> None:
    report = _monitor(make_store()).report()
    assert report.version == "1.0.0"


def test_report_uptime_from_operations() -> None:
    report = _monitor(make_store()).report()
    assert report.uptime_seconds == 3600


def test_report_as_of_set() -> None:
    report = _monitor(make_store()).report()
    assert report.as_of is not None


def test_persistence_metrics_count() -> None:
    report = _monitor(make_store()).report()
    assert report.component("persistence").metrics["stored_reports"] == 7
