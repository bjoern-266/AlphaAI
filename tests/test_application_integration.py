"""End-to-End-Integrationstests des Backend-Dienstes (Sprint 17)."""

from __future__ import annotations

import importlib.util
import json
from datetime import UTC, datetime

import pytest

from application.api.router import ApiRequest
from application.repositories import ReportStore
from engines.application_engine import ApplicationEngine, load_application_rules_from_dict
from models.application import ReportKind
from tests.application_helpers import (
    FakeOperations,
    analytics_payload,
    discovery_payload,
    opportunities_payload,
    recommendations_payload,
)

_NOW = datetime(2026, 7, 12, 14, 0, tzinfo=UTC)
_FASTAPI_AVAILABLE = importlib.util.find_spec("fastapi") is not None

_RULES = {
    "service": {"name": "AlphaAI", "api_version": "v1"},
    "persistence": {"database_file": "r.db"},
    "api": {"auth_policy": "open"},
    "meta": {"version": 1},
}


def _full_engine(store: ReportStore) -> ApplicationEngine:
    """Baut eine Engine, deren Quellen alle Report-Arten liefern."""
    sources = {
        ReportKind.OPPORTUNITIES.value: opportunities_payload,
        ReportKind.DISCOVERY.value: discovery_payload,
        ReportKind.RECOMMENDATIONS.value: recommendations_payload,
        ReportKind.ANALYTICS.value: analytics_payload,
    }
    return ApplicationEngine(
        load_application_rules_from_dict(_RULES),
        store=store,
        operations=FakeOperations(),
        report_sources=sources,
        clock=lambda: _NOW,
    )


def _get(engine: ApplicationEngine, path: str, **query) -> object:
    response = engine.handle(ApiRequest(path=path, query=query, client_host="127.0.0.1"))
    assert response.status == 200, f"{path} -> {response.status}"
    return response.envelope.data


def test_full_cycle_serves_all_reports() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    assert _get(engine, "/operations")["current_session"] == "USA"
    assert _get(engine, "/opportunities")["opportunities"][0]["ticker"] == "AAPL"
    assert _get(engine, "/discovery")["opportunities"][0]["ticker"] == "NVDA"
    assert _get(engine, "/recommendations")["metadata"]["symbol"] == "AAPL"
    assert _get(engine, "/analytics")["result"]["trade_count"] == 10


def test_full_cycle_ticker_filters() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    assert _get(engine, "/opportunities/MSFT")["ticker"] == "MSFT"
    assert _get(engine, "/recommendations/NVDA")["ticker"] == "NVDA"


def test_dashboard_reflects_all() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    dashboard = _get(engine, "/dashboard")
    assert dashboard["opportunities"] is not None
    assert dashboard["discovery"] is not None
    assert dashboard["analytics"] is not None


def test_persistence_survives_restart(tmp_path) -> None:
    db = tmp_path / "reports.db"
    engine = _full_engine(ReportStore(db))
    engine.start(_NOW)
    engine.store.close()

    # Neustart: neue Engine auf derselben Datenbank liefert den letzten Scan.
    reopened = ReportStore(db)
    restarted = ApplicationEngine(
        load_application_rules_from_dict(_RULES),
        store=reopened,
        clock=lambda: _NOW,
    )
    data = _get(restarted, "/opportunities")
    assert data["opportunities"][0]["ticker"] == "AAPL"


def test_last_successful_scan_always_available() -> None:
    store = ReportStore(":memory:")
    engine = _full_engine(store)
    engine.start(_NOW)
    # Ein späterer fehlerhafter Takt darf den letzten Stand nicht löschen.
    broken = ApplicationEngine(
        load_application_rules_from_dict(_RULES),
        store=store,
        operations=FakeOperations(fail=True),
        clock=lambda: _NOW,
    )
    broken.tick(_NOW)
    assert _get(engine, "/opportunities")["opportunities"][0]["ticker"] == "AAPL"


def test_health_ok_after_full_cycle() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    engine.handle(ApiRequest(path="/version", client_host="127.0.0.1"))
    report = engine.health()
    assert report.component("persistence").status.value == "ok"
    assert report.component("api").status.value == "ok"


def test_health_endpoint_serialized() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    data = _get(engine, "/health")
    assert "components" in data
    assert isinstance(data["components"], list)


def test_json_output_is_pure_json() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    response = engine.handle(ApiRequest(path="/opportunities", client_host="127.0.0.1"))
    parsed = json.loads(response.json_bytes())
    assert parsed["ok"] is True
    assert parsed["meta"]["kind"] == "opportunities"


def test_version_endpoint() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    assert _get(engine, "/version")["api_version"] == "v1"


def test_status_endpoint_counts() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    status = _get(engine, "/status")
    assert status["stored_reports"]["operations"] == 1


def test_market_status_endpoint() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    # Der FakeOperations-Report hat keine Marktuhr ⇒ leere, aber gültige Struktur.
    data = _get(engine, "/market-status")
    assert "open_markets" in data


def test_fastapi_adapter_when_unavailable() -> None:
    if _FASTAPI_AVAILABLE:
        pytest.skip("FastAPI ist installiert – Fehlerpfad nicht anwendbar.")
    engine = _full_engine(ReportStore(":memory:"))
    with pytest.raises(RuntimeError):
        engine.create_fastapi_app()


@pytest.mark.skipif(not _FASTAPI_AVAILABLE, reason="FastAPI nicht installiert")
def test_fastapi_adapter_builds_app() -> None:
    engine = _full_engine(ReportStore(":memory:"))
    engine.start(_NOW)
    app = engine.create_fastapi_app()
    assert app is not None


def test_no_business_logic_leak_in_api_payload() -> None:
    # Die API liefert exakt die gespeicherten Felder – kein neu berechnetes Feld.
    store = ReportStore(":memory:")
    engine = _full_engine(store)
    engine.start(_NOW)
    stored = store.latest(ReportKind.OPPORTUNITIES.value).payload
    served = _get(engine, "/opportunities")
    assert served == stored
