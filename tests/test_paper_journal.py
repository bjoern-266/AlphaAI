"""Tests für das automatische Journal (paper_trading.journal)."""

from __future__ import annotations

from datetime import UTC, datetime

from models.paper_trading import CloseReason, OrderAction
from paper_trading import position as pos_mod
from paper_trading.journal import PaperJournal
from tests.helpers import make_paper_position

_TS = datetime(2023, 1, 1, tzinfo=UTC)


def test_record_open_entry():
    journal = PaperJournal()
    entry = journal.record_open(make_paper_position(), _TS)
    assert entry.action is OrderAction.OPEN
    assert entry.exit_price == 0.0
    assert entry.pnl == 0.0
    assert len(journal) == 1


def test_record_close_entry_has_pnl():
    journal = PaperJournal()
    pos = make_paper_position(entry_price=100.0, shares=10.0)
    closed = pos_mod.close_position(pos, 106.0, _TS, CloseReason.TAKE_PROFIT)
    entry = journal.record_close(closed)
    assert entry.action is OrderAction.CLOSE
    assert entry.exit_price == 106.0
    assert entry.pnl == 60.0


def test_record_close_expire_uses_expire_action():
    journal = PaperJournal()
    pos = make_paper_position()
    closed = pos_mod.close_position(pos, 101.0, _TS, CloseReason.EXPIRE)
    entry = journal.record_close(closed)
    assert entry.action is OrderAction.EXPIRE


def test_record_cancel_entry():
    journal = PaperJournal()
    entry = journal.record_cancel(make_paper_position(), _TS)
    assert entry.action is OrderAction.CANCEL


def test_journal_entries_carry_transparency():
    journal = PaperJournal()
    journal.record_open(make_paper_position(recommendation_id="rec:7"), _TS)
    entry = journal.entries()[0]
    assert entry.recommendation_id == "rec:7"
    assert entry.direction and entry.recommendation_strength
    assert entry.reasons == ["Testgrund"]


def test_journal_entry_ids_are_sequential():
    journal = PaperJournal()
    journal.record_open(make_paper_position(), _TS)
    journal.record_open(make_paper_position(position_id="pos:AAPL:2"), _TS)
    ids = [e.entry_id for e in journal.entries()]
    assert ids == ["journal:0", "journal:1"]


def test_journal_entries_returns_copy():
    journal = PaperJournal()
    journal.record_open(make_paper_position(), _TS)
    entries = journal.entries()
    entries.clear()
    assert len(journal) == 1


def test_empty_journal():
    assert len(PaperJournal()) == 0


def test_close_entry_reason_mentions_cause():
    journal = PaperJournal()
    pos = make_paper_position()
    closed = pos_mod.close_position(pos, 96.0, _TS, CloseReason.STOP)
    entry = journal.record_close(closed)
    assert "stop" in entry.reason.lower()
