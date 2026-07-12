"""Tests der unveränderlichen Application-Modelle (Sprint 17)."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from models.application import (
    ApiEnvelope,
    ApiError,
    ApiVersion,
    ComponentHealth,
    EndpointInfo,
    HealthReport,
    HealthStatus,
    ReportKind,
    ServiceInfo,
    StoredReport,
)


def test_report_kind_values_are_stable() -> None:
    assert ReportKind.OPERATIONS.value == "operations"
    assert ReportKind.OPPORTUNITIES.value == "opportunities"
    assert ReportKind.DASHBOARD.value == "dashboard"


def test_report_kind_has_eight_kinds() -> None:
    assert len(list(ReportKind)) == 8


def test_health_status_values() -> None:
    assert {s.value for s in HealthStatus} == {"ok", "degraded", "error", "unknown"}


def test_api_version_defaults() -> None:
    version = ApiVersion()
    assert version.api == "v1"
    assert version.service == "1.0.0"


def test_service_info_defaults() -> None:
    info = ServiceInfo()
    assert info.name == "AlphaAI Backend"
    assert info.api_version == "v1"
    assert info.uptime_seconds is None


def test_component_health_defaults_unknown() -> None:
    component = ComponentHealth(name="cache")
    assert component.status is HealthStatus.UNKNOWN
    assert component.metrics == {}


def test_health_report_healthy_property() -> None:
    assert HealthReport(status=HealthStatus.OK).healthy is True
    assert HealthReport(status=HealthStatus.DEGRADED).healthy is False


def test_health_report_component_lookup() -> None:
    api = ComponentHealth(name="api", status=HealthStatus.OK)
    cache = ComponentHealth(name="cache", status=HealthStatus.DEGRADED)
    report = HealthReport(status=HealthStatus.DEGRADED, components=(api, cache))
    assert report.component("cache") is cache
    assert report.component("missing") is None


def test_stored_report_fields() -> None:
    now = datetime(2026, 7, 12, tzinfo=UTC)
    report = StoredReport(kind="operations", created_at=now, payload={"a": 1}, sequence=3)
    assert report.kind == "operations"
    assert report.sequence == 3
    assert report.payload == {"a": 1}


def test_api_error_detail_default() -> None:
    error = ApiError(status=404, code="not_found", message="fehlt")
    assert error.detail == {}


def test_api_envelope_fields() -> None:
    envelope = ApiEnvelope(ok=True, data={"x": 1}, meta={"kind": "operations"})
    assert envelope.ok is True
    assert envelope.error is None
    assert envelope.meta["kind"] == "operations"


def test_endpoint_info_defaults() -> None:
    info = EndpointInfo(method="GET", path="/health", name="health")
    assert info.report_kind == ""
    assert info.description == ""


@pytest.mark.parametrize(
    ("model", "field"),
    [
        (ApiVersion(), "api"),
        (ServiceInfo(), "name"),
        (ComponentHealth(name="x"), "name"),
        (HealthReport(), "status"),
        (StoredReport(kind="k", created_at=datetime(2026, 1, 1, tzinfo=UTC), payload={}), "kind"),
        (ApiError(status=400, code="c", message="m"), "code"),
        (ApiEnvelope(ok=True), "ok"),
        (EndpointInfo(method="GET", path="/", name="root"), "name"),
    ],
)
def test_models_are_frozen(model: object, field: str) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(model, field, "mutated")


def test_health_report_defaults() -> None:
    report = HealthReport()
    assert report.status is HealthStatus.UNKNOWN
    assert report.components == ()
    assert report.version == ""
