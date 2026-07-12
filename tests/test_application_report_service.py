"""Tests des Lesedienstes für gespeicherte Reports (Sprint 17)."""

from __future__ import annotations

import pytest

from application.exceptions import (
    InvalidRequestError,
    ReportNotFoundError,
    ServiceUnavailableError,
)
from application.services import ReportService
from models.application import ReportKind
from tests.application_helpers import make_store


def _service(populate: bool = True) -> ReportService:
    return ReportService(make_store(populate=populate))


def test_stored_returns_report() -> None:
    service = _service()
    stored = service.stored(ReportKind.OPERATIONS)
    assert stored.kind == "operations"


def test_stored_accepts_string_kind() -> None:
    service = _service()
    assert service.stored("operations").kind == "operations"


def test_stored_raises_when_missing() -> None:
    service = _service(populate=False)
    with pytest.raises(ServiceUnavailableError):
        service.stored(ReportKind.OPERATIONS)


def test_has_true_and_false() -> None:
    service = _service()
    assert service.has(ReportKind.OPERATIONS) is True
    empty = _service(populate=False)
    assert empty.has(ReportKind.OPERATIONS) is False


def test_operations_payload() -> None:
    service = _service()
    assert service.operations()["current_session"] == "USA: open"


def test_scheduler_fields() -> None:
    service = _service()
    scheduler = service.scheduler()
    assert scheduler["next_scan_job"] == "discovery_us"
    assert scheduler["scan_count"] == 4
    assert "job_history" in scheduler


def test_markets_list() -> None:
    service = _service()
    markets = service.markets()
    assert len(markets) == 2
    assert markets[0]["key"] == "us"


def test_market_status_summary() -> None:
    service = _service()
    status = service.market_status()
    assert status["open_markets"] == ["us"]
    assert status["next_open_market"] == "europe"


def test_opportunities_full() -> None:
    service = _service()
    report = service.opportunities()
    assert len(report["opportunities"]) == 2


def test_top_opportunities_limit() -> None:
    service = _service()
    top = service.top_opportunities(1)
    assert len(top) == 1
    assert top[0]["ticker"] == "AAPL"


def test_top_opportunities_more_than_available() -> None:
    service = _service()
    assert len(service.top_opportunities(50)) == 2


def test_top_opportunities_invalid_limit_zero() -> None:
    service = _service()
    with pytest.raises(InvalidRequestError):
        service.top_opportunities(0)


def test_top_opportunities_invalid_limit_negative() -> None:
    service = _service()
    with pytest.raises(InvalidRequestError):
        service.top_opportunities(-3)


def test_opportunity_by_ticker_found() -> None:
    service = _service()
    assert service.opportunity("MSFT")["ticker"] == "MSFT"


def test_opportunity_by_ticker_case_insensitive() -> None:
    service = _service()
    assert service.opportunity("aapl")["ticker"] == "AAPL"


def test_opportunity_by_ticker_missing() -> None:
    service = _service()
    with pytest.raises(ReportNotFoundError):
        service.opportunity("ZZZ")


def test_opportunity_empty_ticker_invalid() -> None:
    service = _service()
    with pytest.raises(InvalidRequestError):
        service.opportunity("   ")


def test_discovery_full() -> None:
    service = _service()
    assert service.discovery()["opportunities"][0]["ticker"] == "NVDA"


def test_recommendations_full() -> None:
    service = _service()
    assert service.recommendations()["metadata"]["symbol"] == "AAPL"


def test_recommendation_by_ticker_from_opportunities() -> None:
    service = _service()
    assert service.recommendation("AAPL")["ticker"] == "AAPL"


def test_recommendation_by_ticker_from_discovery() -> None:
    service = _service()
    assert service.recommendation("NVDA")["ticker"] == "NVDA"


def test_recommendation_by_ticker_missing() -> None:
    service = _service()
    with pytest.raises(ReportNotFoundError):
        service.recommendation("ZZZ")


def test_analytics_backtesting_paper_trading() -> None:
    service = _service()
    assert service.analytics()["result"]["trade_count"] == 10
    assert service.backtesting()["results"][0]["profit_factor"] == 1.5
    assert service.paper_trading()["performance"]["current_equity"] == 10500.0


def test_dashboard_bundles_all_reports() -> None:
    service = _service()
    dashboard = service.dashboard()
    assert dashboard["operations"] is not None
    assert dashboard["opportunities"] is not None
    assert dashboard["analytics"] is not None
    assert "dashboard" not in dashboard


def test_dashboard_partial_reports() -> None:
    store = make_store(populate=False)
    store.save(ReportKind.OPERATIONS.value, {"current_session": "x"})
    service = ReportService(store)
    dashboard = service.dashboard()
    assert dashboard["operations"] is not None
    assert dashboard["discovery"] is None


def test_dashboard_unavailable_when_empty() -> None:
    service = _service(populate=False)
    with pytest.raises(ServiceUnavailableError):
        service.dashboard()


def test_missing_analytics_raises_unavailable() -> None:
    store = make_store(populate=False)
    store.save(ReportKind.OPERATIONS.value, {"current_session": "x"})
    service = ReportService(store)
    with pytest.raises(ServiceUnavailableError):
        service.analytics()
