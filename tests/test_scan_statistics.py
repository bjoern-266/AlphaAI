"""Tests für ScanStatistics."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from scanner.scan_statistics import ScanStatistics


class SteppingClock:
    """Zeitquelle, die bei jedem Aufruf um eine feste Spanne fortschreitet."""

    def __init__(self, step_seconds: float = 1.0) -> None:
        self._current = datetime(2024, 1, 1, tzinfo=UTC)
        self._step = timedelta(seconds=step_seconds)

    def __call__(self) -> datetime:
        value = self._current
        self._current += self._step
        return value


def test_runtime_zero_without_finish() -> None:
    stats = ScanStatistics()
    stats.start()
    assert stats.runtime_seconds == 0.0


def test_runtime_measured() -> None:
    stats = ScanStatistics(now_fn=SteppingClock(step_seconds=5.0))
    stats.start()  # t=0
    stats.finish()  # t=5
    assert stats.runtime_seconds == 5.0


def test_record_counts_cache_hits_and_misses() -> None:
    stats = ScanStatistics()
    stats.record_symbol(cache_hit=True)
    stats.record_symbol(cache_hit=False)
    stats.record_symbol(cache_hit=False)
    assert stats.cache_hits == 1
    assert stats.cache_misses == 2
    assert stats.symbol_count == 3


def test_record_tracks_errors() -> None:
    stats = ScanStatistics()
    stats.record_symbol(cache_hit=False, error_message="Fehler A")
    assert stats.error_count == 1
    assert stats.error_messages == ["Fehler A"]


def test_to_dict_contains_all_fields() -> None:
    stats = ScanStatistics(provider="yahoo", now_fn=SteppingClock())
    stats.start()
    stats.record_symbol(cache_hit=True)
    stats.finish()
    data = stats.to_dict()
    for key in (
        "provider",
        "start_time",
        "end_time",
        "runtime_seconds",
        "symbol_count",
        "cache_hits",
        "cache_misses",
        "error_count",
    ):
        assert key in data
    assert data["provider"] == "yahoo"
