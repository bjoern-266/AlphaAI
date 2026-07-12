"""Tests der einheitlichen API-Antwort-Hüllen (Sprint 17)."""

from __future__ import annotations

from application.exceptions import ReportNotFoundError
from application.responses import error_envelope, error_from_exception, success_envelope


def test_success_envelope_ok() -> None:
    envelope = success_envelope({"x": 1})
    assert envelope.ok is True
    assert envelope.data == {"x": 1}
    assert envelope.error is None


def test_success_envelope_has_api_version_meta() -> None:
    envelope = success_envelope([], api_version="v2")
    assert envelope.meta["api_version"] == "v2"
    assert "generated_at" in envelope.meta


def test_success_envelope_merges_extra_meta() -> None:
    envelope = success_envelope({}, meta={"kind": "operations"})
    assert envelope.meta["kind"] == "operations"
    assert "generated_at" in envelope.meta


def test_error_envelope_not_ok() -> None:
    envelope = error_envelope(status=404, code="not_found", message="fehlt")
    assert envelope.ok is False
    assert envelope.data is None
    assert envelope.error is not None


def test_error_envelope_fields() -> None:
    envelope = error_envelope(status=400, code="invalid_request", message="bad", detail={"p": 1})
    assert envelope.error.status == 400
    assert envelope.error.code == "invalid_request"
    assert envelope.error.detail == {"p": 1}


def test_error_from_exception_maps_status_and_code() -> None:
    error = ReportNotFoundError("nicht da", detail={"ticker": "ZZZ"})
    envelope = error_from_exception(error)
    assert envelope.error.status == 404
    assert envelope.error.code == "not_found"
    assert envelope.error.detail == {"ticker": "ZZZ"}


def test_error_from_exception_message() -> None:
    envelope = error_from_exception(ReportNotFoundError("nicht da"))
    assert envelope.error.message == "nicht da"


def test_error_envelope_default_detail_empty() -> None:
    envelope = error_envelope(status=503, code="service_unavailable", message="warte")
    assert envelope.error.detail == {}


def test_success_envelope_default_api_version() -> None:
    envelope = success_envelope(None)
    assert envelope.meta["api_version"] == "v1"


def test_error_from_exception_uses_api_version() -> None:
    envelope = error_from_exception(ReportNotFoundError("x"), api_version="v3")
    assert envelope.meta["api_version"] == "v3"
