"""Tests der ApplicationEngine (Composition Root) und Regeln (Sprint 17)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from application.api.router import ApiRequest
from application.repositories import ReportStore
from engines.application_engine import (
    ApplicationEngine,
    ApplicationRulesError,
    load_application_rules,
    load_application_rules_from_dict,
)
from engines.application_registry import build_default_registry
from models.application import ReportKind
from tests.application_helpers import FakeOperations

_NOW = datetime(2026, 7, 12, 14, 0, tzinfo=UTC)

_VALID_RULES = {
    "service": {"name": "AlphaAI", "version": "1.0.0", "api_version": "v1", "environment": "local"},
    "persistence": {"database_file": "reports.db", "retention": 50},
    "api": {"cache_capacity": 64, "default_top_limit": 5, "auth_policy": "open"},
    "meta": {"version": 2},
}


# ------------------------------------------------------------------ Regeln
def test_load_rules_from_file() -> None:
    rules = load_application_rules()
    assert rules.service.name == "AlphaAI Backend"
    assert rules.auth_policy == "local_only"
    assert rules.cache_capacity >= 1


def test_rules_from_dict_valid() -> None:
    rules = load_application_rules_from_dict(_VALID_RULES)
    assert rules.service.version == "1.0.0"
    assert rules.retention == 50
    assert rules.default_top_limit == 5
    assert rules.version == 2


def test_rules_unknown_auth_policy() -> None:
    data = {**_VALID_RULES, "api": {**_VALID_RULES["api"], "auth_policy": "cloud"}}
    with pytest.raises(ApplicationRulesError):
        load_application_rules_from_dict(data)


def test_rules_empty_database_file() -> None:
    data = {**_VALID_RULES, "persistence": {"database_file": ""}}
    with pytest.raises(ApplicationRulesError):
        load_application_rules_from_dict(data)


def test_rules_negative_retention() -> None:
    data = {**_VALID_RULES, "persistence": {"database_file": "r.db", "retention": -1}}
    with pytest.raises(ApplicationRulesError):
        load_application_rules_from_dict(data)


def test_rules_zero_cache_capacity() -> None:
    data = {**_VALID_RULES, "api": {**_VALID_RULES["api"], "cache_capacity": 0}}
    with pytest.raises(ApplicationRulesError):
        load_application_rules_from_dict(data)


def test_rules_zero_top_limit() -> None:
    data = {**_VALID_RULES, "api": {**_VALID_RULES["api"], "default_top_limit": 0}}
    with pytest.raises(ApplicationRulesError):
        load_application_rules_from_dict(data)


def test_rules_defaults_applied() -> None:
    rules = load_application_rules_from_dict({"persistence": {"database_file": "r.db"}})
    assert rules.auth_policy == "local_only"
    assert rules.cache_capacity == 256


def test_load_rules_missing_file(tmp_path) -> None:
    with pytest.raises(ApplicationRulesError):
        load_application_rules(tmp_path / "missing.toml")


# ------------------------------------------------------------ Registry
def test_default_registry_has_all_kinds() -> None:
    registry = build_default_registry()
    assert len(registry) == 8
    for kind in ReportKind:
        assert kind.value in registry


def test_registry_dashboard_is_composite() -> None:
    registry = build_default_registry()
    assert registry.get(ReportKind.DASHBOARD.value).composite is True


# ------------------------------------------------------------- Engine
def _engine(**kwargs) -> ApplicationEngine:
    store = kwargs.pop("store", ReportStore(":memory:"))
    return ApplicationEngine(
        load_application_rules_from_dict(_VALID_RULES),
        store=store,
        clock=lambda: _NOW,
        **kwargs,
    )


def test_engine_builds_without_operations() -> None:
    engine = _engine()
    assert engine.background is None
    assert engine.api is not None


def test_engine_start_requires_operations() -> None:
    engine = _engine()
    with pytest.raises(ApplicationRulesError):
        engine.start(_NOW)


def test_engine_tick_requires_operations() -> None:
    engine = _engine()
    with pytest.raises(ApplicationRulesError):
        engine.tick(_NOW)


def test_engine_with_operations_start() -> None:
    engine = _engine(operations=FakeOperations())
    result = engine.start(_NOW)
    assert result.ok is True
    assert ReportKind.OPERATIONS.value in result.stored_kinds


def test_engine_handle_after_start() -> None:
    engine = _engine(operations=FakeOperations())
    engine.start(_NOW)
    response = engine.handle(ApiRequest(path="/operations", client_host="127.0.0.1"))
    assert response.status == 200


def test_engine_health_reflects_cache() -> None:
    engine = _engine(operations=FakeOperations())
    engine.start(_NOW)
    # Zwei Anfragen erzeugen Cache-Verkehr, den der Health-Monitor liest.
    engine.handle(ApiRequest(path="/version", client_host="127.0.0.1"))
    report = engine.health()
    cache = report.component("cache")
    assert cache is not None
    assert "hits" in cache.metrics


def test_engine_registry_exposed() -> None:
    engine = _engine()
    assert len(engine.registry) == 8


def test_engine_store_exposed() -> None:
    store = ReportStore(":memory:")
    engine = _engine(store=store)
    assert engine.store is store


def test_engine_reports_service_exposed() -> None:
    engine = _engine(operations=FakeOperations())
    engine.start(_NOW)
    assert engine.reports.has(ReportKind.OPERATIONS)


def test_engine_from_config_with_injected_store() -> None:
    store = ReportStore(":memory:")
    engine = ApplicationEngine.from_config(
        store=store, operations=FakeOperations(), clock=lambda: _NOW
    )
    result = engine.start(_NOW)
    assert result.ok is True


def test_engine_report_sources_persisted() -> None:
    engine = _engine(
        operations=FakeOperations(),
        report_sources={ReportKind.ANALYTICS.value: lambda: {"result": {"trade_count": 9}}},
    )
    engine.start(_NOW)
    response = engine.handle(ApiRequest(path="/analytics", client_host="127.0.0.1"))
    assert response.envelope.data["result"]["trade_count"] == 9


def test_engine_local_only_from_config_rejects_remote() -> None:
    # Standardregeln nutzen local_only; ein entfernter Host wird abgewiesen.
    store = ReportStore(":memory:")
    engine = ApplicationEngine.from_config(store=store, clock=lambda: _NOW)
    response = engine.handle(ApiRequest(path="/version", client_host="8.8.8.8"))
    assert response.status == 401


def test_engine_multiple_ticks_update_store() -> None:
    engine = _engine(operations=FakeOperations())
    engine.start(_NOW)
    engine.tick(_NOW)
    assert engine.store.count(ReportKind.OPERATIONS.value) == 2
