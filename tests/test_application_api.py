"""Tests der API-Fassade (Routing, Zugriffskontrolle, Cache) (Sprint 17)."""

from __future__ import annotations

from application.api import ApplicationApi
from application.api.router import ApiRequest
from application.api.routes import build_router
from application.authentication import LocalOnlyPolicy
from application.health import HealthMonitor
from application.services import ReportService, SystemService
from models.application import ReportKind
from tests.application_helpers import make_api, make_store, opportunities_payload


def _request(path: str, **kwargs) -> ApiRequest:
    return ApiRequest(path=path, client_host="127.0.0.1", **kwargs)


def test_all_endpoints_registered() -> None:
    api = make_api()
    paths = {info.path for info in api.endpoints()}
    for expected in [
        "/health",
        "/status",
        "/version",
        "/scheduler",
        "/operations",
        "/markets",
        "/market-status",
        "/opportunities",
        "/opportunities/top",
        "/opportunities/{ticker}",
        "/discovery",
        "/recommendations",
        "/recommendations/{ticker}",
        "/analytics",
        "/backtesting",
        "/paper-trading",
        "/dashboard",
    ]:
        assert expected in paths


def test_health_endpoint() -> None:
    response = make_api().handle(_request("/health"))
    assert response.status == 200
    assert response.envelope.data["status"] in {"ok", "degraded", "unknown", "error"}


def test_operations_endpoint() -> None:
    response = make_api().handle(_request("/operations"))
    assert response.envelope.data["current_session"] == "USA: open"


def test_opportunity_ticker_endpoint() -> None:
    response = make_api().handle(_request("/opportunities/AAPL"))
    assert response.envelope.data["ticker"] == "AAPL"


def test_opportunity_ticker_missing_404() -> None:
    response = make_api().handle(_request("/opportunities/ZZZ"))
    assert response.status == 404


def test_top_limit_query() -> None:
    response = make_api().handle(_request("/opportunities/top", query={"limit": "1"}))
    assert len(response.envelope.data) == 1


def test_top_invalid_limit_400() -> None:
    response = make_api().handle(_request("/opportunities/top", query={"limit": "abc"}))
    assert response.status == 400


def test_missing_report_503() -> None:
    api = make_api(make_store(populate=False))
    response = api.handle(_request("/operations"))
    assert response.status == 503


def test_unknown_path_404() -> None:
    response = make_api().handle(_request("/does-not-exist"))
    assert response.status == 404


def test_local_only_rejects_remote() -> None:
    store = make_store()
    reports = ReportService(store)
    system = SystemService(store)
    health = HealthMonitor(store)
    api = ApplicationApi(
        build_router(reports, system, health), store, auth_policy=LocalOnlyPolicy()
    )
    response = api.handle(ApiRequest(path="/version", client_host="8.8.8.8"))
    assert response.status == 401
    assert response.envelope.error.code == "unauthorized"


def test_local_only_allows_loopback() -> None:
    store = make_store()
    reports = ReportService(store)
    system = SystemService(store)
    health = HealthMonitor(store)
    api = ApplicationApi(
        build_router(reports, system, health), store, auth_policy=LocalOnlyPolicy()
    )
    response = api.handle(ApiRequest(path="/version", client_host="127.0.0.1"))
    assert response.status == 200


def test_cache_hit_on_repeat() -> None:
    api = make_api()
    first = api.handle(_request("/operations"))
    second = api.handle(_request("/operations"))
    assert first.cached is False
    assert second.cached is True


def test_cache_metrics_increment() -> None:
    api = make_api()
    api.handle(_request("/operations"))
    api.handle(_request("/operations"))
    metrics = api.cache_metrics()
    assert metrics["hits"] >= 1


def test_cache_invalidated_on_new_report() -> None:
    store = make_store()
    api = make_api(store)
    api.handle(_request("/operations"))
    # Neuer Report ⇒ Revision ändert sich ⇒ Cache-Miss (frischer Stand).
    payload = opportunities_payload()
    store.save(ReportKind.OPERATIONS.value, payload)
    response = api.handle(_request("/operations"))
    assert response.cached is False


def test_errors_not_cached() -> None:
    api = make_api()
    api.handle(_request("/opportunities/ZZZ"))
    second = api.handle(_request("/opportunities/ZZZ"))
    assert second.cached is False


def test_clear_cache() -> None:
    api = make_api()
    api.handle(_request("/operations"))
    api.clear_cache()
    response = api.handle(_request("/operations"))
    assert response.cached is False


def test_different_query_separate_cache() -> None:
    api = make_api()
    api.handle(_request("/opportunities/top", query={"limit": "1"}))
    second = api.handle(_request("/opportunities/top", query={"limit": "2"}))
    assert second.cached is False


def test_open_policy_allows_remote() -> None:
    api = make_api()  # OpenPolicy
    response = api.handle(ApiRequest(path="/version", client_host="8.8.8.8"))
    assert response.status == 200


def test_json_bytes_contains_envelope() -> None:
    response = make_api().handle(_request("/version"))
    raw = response.json_bytes().decode("utf-8")
    assert '"ok":true' in raw
    assert '"data"' in raw


def test_dashboard_endpoint_bundles() -> None:
    response = make_api().handle(_request("/dashboard"))
    assert response.envelope.data["operations"] is not None


def test_scheduler_endpoint() -> None:
    response = make_api().handle(_request("/scheduler"))
    assert response.envelope.data["next_scan_job"] == "discovery_us"


def test_markets_endpoint() -> None:
    response = make_api().handle(_request("/markets"))
    assert len(response.envelope.data) == 2
