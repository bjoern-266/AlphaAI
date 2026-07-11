"""Tests für die Journal-Analyse und die Summary-Analyse."""

from __future__ import annotations

from datetime import UTC, datetime

from analytics.journal_analysis import JournalAnalysisModel
from analytics.summary_analysis import SummaryAnalysisModel
from models.paper_trading import JournalEntry, OrderAction
from models.recommendation import Direction, RecommendationStrength
from tests.helpers import make_analytics_context, make_analytics_trade

_TS = datetime(2023, 1, 1, tzinfo=UTC)


def _entry(action: OrderAction, pnl: float = 0.0):
    return JournalEntry(
        entry_id=f"j:{action.value}",
        position_id="pos:1",
        recommendation_id="rec:1",
        action=action,
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.HIGH,
        entry_price=100.0,
        exit_price=105.0 if action is not OrderAction.OPEN else 0.0,
        reason="test",
        pnl=pnl,
        timestamp=_TS,
    )


def test_journal_counts_actions():
    journal = [_entry(OrderAction.OPEN), _entry(OrderAction.CLOSE, 50.0)]
    out = JournalAnalysisModel().compute(make_analytics_context(journal=journal), {})
    stats = out.statistics["journal"]
    assert stats["action_counts"]["open"] == 1
    assert stats["action_counts"]["close"] == 1
    assert stats["total_entries"] == 2


def test_journal_winners_losers():
    journal = [
        _entry(OrderAction.CLOSE, 50.0),
        _entry(OrderAction.CLOSE, -20.0),
        _entry(OrderAction.EXPIRE, 10.0),
    ]
    out = JournalAnalysisModel().compute(make_analytics_context(journal=journal), {})
    stats = out.statistics["journal"]
    assert stats["winners"] == 2
    assert stats["losers"] == 1
    assert stats["realized_pnl"] == 40.0


def test_journal_closed_entries_count():
    journal = [_entry(OrderAction.CLOSE, 10.0), _entry(OrderAction.EXPIRE, 5.0)]
    out = JournalAnalysisModel().compute(make_analytics_context(journal=journal), {})
    assert out.statistics["journal"]["closed_entries"] == 2


def test_journal_empty_warns():
    out = JournalAnalysisModel().compute(make_analytics_context(journal=[]), {})
    assert out.warnings
    assert out.statistics["journal"]["total_entries"] == 0


def test_journal_metric_total_entries():
    journal = [_entry(OrderAction.OPEN)]
    out = JournalAnalysisModel().compute(make_analytics_context(journal=journal), {})
    assert out.metrics["total_entries"] == 1.0


def test_journal_only_reads_no_mutation():
    journal = [_entry(OrderAction.OPEN)]
    JournalAnalysisModel().compute(make_analytics_context(journal=journal), {})
    # Journal-Liste unverändert (nur Lesen).
    assert len(journal) == 1


# --- Summary ----------------------------------------------------------------
def test_summary_text_for_trades():
    out = SummaryAnalysisModel().compute(
        make_analytics_context(trades=[make_analytics_trade(pnl=100.0)]), {}
    )
    assert "Trades ausgewertet" in out.details["summary"]
    assert "Win Rate" in out.details["summary"]


def test_summary_empty():
    out = SummaryAnalysisModel().compute(make_analytics_context(trades=[]), {})
    assert "Keine Trades" in out.details["summary"]


def test_summary_mentions_long_short():
    trades = [
        make_analytics_trade(direction=Direction.LONG),
        make_analytics_trade(direction=Direction.SHORT),
    ]
    out = SummaryAnalysisModel().compute(make_analytics_context(trades=trades), {})
    assert "LONG 1 / SHORT 1" in out.details["summary"]


def test_summary_reason_equals_summary():
    out = SummaryAnalysisModel().compute(make_analytics_context(), {})
    assert out.reasons[0] == out.details["summary"]
