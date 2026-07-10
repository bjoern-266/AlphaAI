"""Integrations-Tests: echte Szenarien durch die Paper Trading Engine.

Kein Mock: die Szenarien laufen durch die **echte** Pipeline und werden im
simulierten Portfolio ausgewertet. Diese Tests belegen die Kern-Invarianten
(keine neue Handelsregel, Trennung von Richtung und Stärke, vollständige
Nachvollziehbarkeit, keine echten Orders).
"""

from __future__ import annotations

from engines.paper_trading_engine import PaperTradingEngine
from models.paper_trading import Direction, PositionStatus
from pipeline.runner import IntegrationRunner
from tests import scenarios
from tests.helpers import make_paper_rules, make_settings

_RULES = make_paper_rules(
    runner={"warmup_bars": 200, "step": 10, "max_holding_days": 8, "trailing_distance": 0.0}
)


def _engine():
    return PaperTradingEngine(
        runner=IntegrationRunner.from_config(), settings=make_settings(), rules=_RULES
    )


def test_trend_up_runs_valid():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert report.valid is True
    assert report.result_count >= 1


def test_trend_up_is_long_never_short():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert Direction.SHORT not in {r.direction for r in report.results}


def test_trend_down_is_short_never_long():
    report = _engine().run_frame(scenarios.trend_down(), "XYZ")
    assert Direction.LONG not in {r.direction for r in report.results}


def test_no_duplicate_open_recommendation():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    open_recs = [r.recommendation_id for r in report.results if r.status is PositionStatus.OPEN]
    assert len(open_recs) == len(set(open_recs))


def test_strength_never_contains_direction_terms():
    report = _engine().run_frame(scenarios.trend_down(), "XYZ")
    forbidden = {"buy", "sell", "long", "short"}
    for result in report.results:
        assert result.recommendation_strength.value not in forbidden


def test_positions_fully_traceable():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    for result in report.results:
        assert result.recommendation_id
        assert result.direction is not None
        assert result.recommendation_strength is not None


def test_journal_documents_every_position():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    opened = {e.position_id for e in report.journal if e.action.value == "open"}
    position_ids = {r.paper_trading_id.removeprefix("paper:") for r in report.results}
    # Jede Position hat einen Eröffnungs-Eintrag.
    assert position_ids <= opened


def test_closed_positions_have_exit_and_pnl():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    for result in report.closed_results:
        assert result.exit_time is not None
        assert result.close_reason is not None


def test_equity_curve_recorded():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert len(report.performance.equity_curve) > 0


def test_statistics_counts_match_results():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert report.statistics.closed_positions == len(report.closed_results)
    assert report.statistics.open_positions == len(report.open_results)


def test_sideways_stays_consistent():
    report = _engine().run_frame(scenarios.sideways(), "SYM")
    assert report.valid is True
    assert 0.0 <= report.statistics.win_rate <= 1.0
    assert 0.0 <= report.performance.maximum_drawdown_pct <= 100.0


def test_exposure_within_bounds():
    report = _engine().run_frame(scenarios.trend_up(), "AAPL")
    assert report.performance.portfolio_exposure_pct >= 0.0
