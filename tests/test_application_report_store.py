"""Tests des dauerhaften SQLite-Report-Speichers (Sprint 17)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from application.repositories import ReportStore
from models.application import StoredReport


def test_save_returns_stored_report() -> None:
    store = ReportStore(":memory:")
    result = store.save("operations", {"a": 1}, report_version=3)
    assert isinstance(result, StoredReport)
    assert result.kind == "operations"
    assert result.report_version == 3
    assert result.sequence >= 1


def test_latest_returns_none_when_empty() -> None:
    store = ReportStore(":memory:")
    assert store.latest("operations") is None


def test_latest_returns_last_saved() -> None:
    store = ReportStore(":memory:")
    store.save("operations", {"n": 1})
    store.save("operations", {"n": 2})
    assert store.latest("operations").payload == {"n": 2}


def test_latest_is_per_kind() -> None:
    store = ReportStore(":memory:")
    store.save("operations", {"k": "ops"})
    store.save("discovery", {"k": "disc"})
    assert store.latest("operations").payload == {"k": "ops"}
    assert store.latest("discovery").payload == {"k": "disc"}


def test_history_newest_first() -> None:
    store = ReportStore(":memory:")
    for i in range(3):
        store.save("operations", {"n": i})
    history = store.history("operations", limit=3)
    assert [h.payload["n"] for h in history] == [2, 1, 0]


def test_history_limit_zero_returns_empty() -> None:
    store = ReportStore(":memory:")
    store.save("operations", {"n": 1})
    assert store.history("operations", limit=0) == ()


def test_history_respects_limit() -> None:
    store = ReportStore(":memory:")
    for i in range(5):
        store.save("operations", {"n": i})
    assert len(store.history("operations", limit=2)) == 2


def test_count_total_and_per_kind() -> None:
    store = ReportStore(":memory:")
    store.save("operations", {})
    store.save("operations", {})
    store.save("discovery", {})
    assert store.count() == 3
    assert store.count("operations") == 2
    assert store.count("discovery") == 1


def test_kinds_sorted() -> None:
    store = ReportStore(":memory:")
    store.save("operations", {})
    store.save("discovery", {})
    assert store.kinds() == ("discovery", "operations")


def test_retention_keeps_only_latest() -> None:
    store = ReportStore(":memory:", retention=2)
    for i in range(5):
        store.save("operations", {"n": i})
    history = store.history("operations", limit=10)
    assert [h.payload["n"] for h in history] == [4, 3]
    assert store.count("operations") == 2


def test_retention_zero_unlimited() -> None:
    store = ReportStore(":memory:", retention=0)
    for i in range(10):
        store.save("operations", {"n": i})
    assert store.count("operations") == 10


def test_retention_is_per_kind() -> None:
    store = ReportStore(":memory:", retention=1)
    store.save("operations", {"n": 1})
    store.save("discovery", {"n": 1})
    store.save("operations", {"n": 2})
    assert store.count("operations") == 1
    assert store.count("discovery") == 1


def test_revision_increases_on_save() -> None:
    store = ReportStore(":memory:")
    start = store.revision
    store.save("operations", {})
    assert store.revision > start


def test_revision_stable_without_save() -> None:
    store = ReportStore(":memory:")
    store.save("operations", {})
    revision = store.revision
    assert store.revision == revision


def test_created_at_preserved() -> None:
    store = ReportStore(":memory:")
    moment = datetime(2026, 7, 12, 9, 0, tzinfo=UTC)
    store.save("operations", {}, created_at=moment)
    assert store.latest("operations").created_at == moment


def test_default_created_at_is_recent() -> None:
    store = ReportStore(":memory:")
    before = datetime.now(UTC) - timedelta(seconds=5)
    store.save("operations", {})
    assert store.latest("operations").created_at >= before


def test_payload_roundtrip_complex() -> None:
    store = ReportStore(":memory:")
    payload = {"a": [1, 2, {"b": "c"}], "d": None, "e": 1.5}
    store.save("operations", payload)
    assert store.latest("operations").payload == payload


def test_persistence_survives_reopen(tmp_path: Path) -> None:
    db = tmp_path / "reports.db"
    store = ReportStore(db)
    store.save("operations", {"n": 42}, report_version=9)
    store.close()

    reopened = ReportStore(db)
    latest = reopened.latest("operations")
    assert latest is not None
    assert latest.payload == {"n": 42}
    assert latest.report_version == 9


def test_revision_restored_after_reopen(tmp_path: Path) -> None:
    db = tmp_path / "reports.db"
    store = ReportStore(db)
    store.save("operations", {})
    store.save("operations", {})
    revision = store.revision
    store.close()

    reopened = ReportStore(db)
    assert reopened.revision == revision


def test_history_missing_kind_empty() -> None:
    store = ReportStore(":memory:")
    assert store.history("unknown") == ()


def test_count_missing_kind_zero() -> None:
    store = ReportStore(":memory:")
    assert store.count("unknown") == 0


@pytest.mark.parametrize("retention", [1, 5, 50])
def test_retention_bound_never_exceeded(retention: int) -> None:
    store = ReportStore(":memory:", retention=retention)
    for i in range(retention + 10):
        store.save("operations", {"n": i})
    assert store.count("operations") == retention
