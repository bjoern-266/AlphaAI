"""Fixtures und Beispiel-Reports für die Application-/API-Tests (Sprint 17).

Die Helfer bauen einen befüllten Report-Speicher sowie eine einsatzbereite
API/Engine mit **offener** Zugriffsrichtlinie (damit Tests keinen lokalen Host
vortäuschen müssen). Die Beispiel-Payloads spiegeln die Struktur der echten,
serialisierten Reports wider.
"""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime
from typing import Any

from application.api import ApplicationApi
from application.api.routes import build_router
from application.authentication import OpenPolicy
from application.health import HealthMonitor
from application.repositories import ReportStore
from application.services import ReportService, SystemService
from models.application import ReportKind

FIXED_NOW = datetime(2026, 7, 12, 14, 30, tzinfo=UTC)


def operations_payload() -> dict[str, Any]:
    """Ein repräsentativer, serialisierter Operations-Report."""
    return {
        "as_of": "2026-07-12T14:30:00+00:00",
        "current_session": "USA: open",
        "market_clock": {
            "as_of": "2026-07-12T14:30:00+00:00",
            "markets": [
                {
                    "key": "us",
                    "title": "USA",
                    "phase": "open",
                    "is_open": True,
                    "next_phase": "close",
                    "seconds_to_next": 3600,
                },
                {
                    "key": "europe",
                    "title": "Europa",
                    "phase": "close",
                    "is_open": False,
                    "next_phase": "pre_market",
                    "seconds_to_next": 60000,
                },
            ],
            "open_markets": ["us"],
            "next_open_market": "europe",
            "next_open_at": "2026-07-13T05:30:00+00:00",
        },
        "last_successful_scan_at": "2026-07-12T14:00:00+00:00",
        "next_scan_at": "2026-07-12T15:00:00+00:00",
        "next_scan_job": "discovery_us",
        "running_job": None,
        "job_history": [
            {
                "name": "discovery_us",
                "job_type": "discovery",
                "status": "success",
                "duration_seconds": 1.5,
                "error": "",
                "summary": "12 Chancen",
            }
        ],
        "system_state": {
            "health": "ok",
            "heartbeat": {"alive": True, "age_seconds": 5, "interval_seconds": 60},
            "running_job": None,
            "queue_size": 0,
            "scan_count": 4,
            "error_count": 0,
            "last_error": "",
            "uptime_seconds": 3600,
        },
        "scan_count": 4,
        "error_count": 0,
        "average_runtime": 1.4,
        "discovery": None,
        "new_opportunities": ["AAPL"],
        "new_risks": [],
        "valid": True,
        "warnings": [],
        "metadata": {"rules_version": 1},
    }


def opportunities_payload() -> dict[str, Any]:
    """Ein repräsentativer, serialisierter Opportunity-Report."""
    return {
        "opportunities": [
            {
                "ticker": "AAPL",
                "company": "Apple",
                "market": "NASDAQ",
                "sector": "Technology",
                "opportunity_rank": 1,
                "opportunity_score": 82.0,
                "direction": "long",
                "recommendation_strength": "high",
                "confidence": 0.8,
                "risk": 70.0,
                "summary": "Starker Aufwärtstrend",
            },
            {
                "ticker": "MSFT",
                "company": "Microsoft",
                "market": "NASDAQ",
                "sector": "Technology",
                "opportunity_rank": 2,
                "opportunity_score": 74.0,
                "direction": "long",
                "recommendation_strength": "medium",
                "confidence": 0.7,
                "risk": 65.0,
                "summary": "Solide Chance",
            },
        ],
        "statistics": {"analyzed_count": 2, "long_count": 2, "short_count": 0},
        "valid": True,
        "warnings": [],
        "metadata": {},
    }


def discovery_payload() -> dict[str, Any]:
    """Ein repräsentativer, serialisierter Discovery-Report."""
    return {
        "opportunities": [
            {
                "ticker": "NVDA",
                "company": "NVIDIA",
                "sector": "Technology",
                "country": "US",
                "market": "nasdaq100",
                "rank": 1,
                "opportunity_score": 88.0,
                "direction": "long",
                "recommendation_strength": "very_high",
                "confidence": 0.9,
                "risk": 72.0,
                "summary": "Top-Chance",
            }
        ],
        "statistics": {"universe_count": 100, "rejected_count": 40, "analyzed_count": 60},
        "markets": ["nasdaq100"],
        "valid": True,
    }


def recommendations_payload() -> dict[str, Any]:
    """Ein repräsentativer, serialisierter Recommendation-Report."""
    return {
        "results": [
            {
                "recommendation_id": "rec-1",
                "direction": "long",
                "recommendation_strength": "high",
                "confidence": 0.8,
                "overall_rating": 80.0,
                "summary": "Kaufkandidat",
                "reasons": ["Trend"],
                "warnings": [],
            }
        ],
        "valid": True,
        "warnings": [],
        "metadata": {"symbol": "AAPL"},
    }


def analytics_payload() -> dict[str, Any]:
    """Ein minimaler, serialisierter Analytics-Report."""
    return {"result": {"trade_count": 10, "win_rate": 0.6, "profit_factor": 1.8}, "valid": True}


def backtesting_payload() -> dict[str, Any]:
    """Ein minimaler, serialisierter Backtesting-Report."""
    return {"results": [{"profit_factor": 1.5, "win_rate": 0.55}], "valid": True}


def paper_trading_payload() -> dict[str, Any]:
    """Ein minimaler, serialisierter Paper-Trading-Report."""
    return {"performance": {"current_equity": 10500.0}, "valid": True}


def make_store(*, populate: bool = True, path: str = ":memory:") -> ReportStore:
    """Baut einen Report-Speicher; ``populate`` legt die Beispiel-Reports an."""
    store = ReportStore(path)
    if populate:
        store.save(ReportKind.OPERATIONS.value, operations_payload(), report_version=1)
        store.save(ReportKind.OPPORTUNITIES.value, opportunities_payload())
        store.save(ReportKind.DISCOVERY.value, discovery_payload())
        store.save(ReportKind.RECOMMENDATIONS.value, recommendations_payload())
        store.save(ReportKind.ANALYTICS.value, analytics_payload())
        store.save(ReportKind.BACKTESTING.value, backtesting_payload())
        store.save(ReportKind.PAPER_TRADING.value, paper_trading_payload())
    return store


def make_api(store: ReportStore | None = None) -> ApplicationApi:
    """Baut eine einsatzbereite API-Fassade mit offener Zugriffsrichtlinie."""
    used = store or make_store()
    reports = ReportService(used)
    system = SystemService(used, clock=lambda: FIXED_NOW)
    health = HealthMonitor(used, version="1.0.0", clock=lambda: FIXED_NOW)
    router = build_router(reports, system, health)
    return ApplicationApi(router, used, auth_policy=OpenPolicy())


class FakeOperations:
    """Duck-getypter Operations-Taktgeber für Hintergrunddienst-Tests."""

    def __init__(self, report: Any = None, *, fail: bool = False) -> None:
        self.report = report if report is not None else _SimpleReport()
        self.fail = fail
        self.beats = 0
        self.ticks = 0

    def beat(self, now: datetime | None = None) -> None:
        """Zählt Heartbeats."""
        self.beats += 1

    def tick(self, now: datetime | None = None) -> Any:
        """Liefert den Report oder wirft (Recovery-Test)."""
        self.ticks += 1
        if self.fail:
            raise RuntimeError("Taktgeber-Fehler")
        return self.report


@dataclasses.dataclass(frozen=True)
class _SimpleReport:
    """Ein minimaler Report mit Metadaten (für Serialisierung/Persistenz)."""

    as_of: str = "2026-07-12T14:30:00+00:00"
    current_session: str = "USA"
    metadata: dict = dataclasses.field(default_factory=lambda: {"rules_version": 7})


__all__ = [
    "FIXED_NOW",
    "operations_payload",
    "opportunities_payload",
    "discovery_payload",
    "recommendations_payload",
    "analytics_payload",
    "backtesting_payload",
    "paper_trading_payload",
    "make_store",
    "make_api",
    "FakeOperations",
]
