"""Fixtures für die Dashboard-Tests (Sprint 13).

Baut **bereits vorhandene** Reports (Recommendation/Paper/Backtest/Analytics)
mit realistischen Werten, damit die reine Presentation Layer gegen echte
Report-Strukturen getestet werden kann. Es findet hier **keine** Fachlogik statt
– nur der Aufbau vorhandener, unveränderlicher Report-Objekte.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from models.analytics import AnalyticsReport, AnalyticsResult, GroupStatistics
from models.backtest import (
    BacktestReport,
    BacktestResult,
    BenchmarkResult,
    EquityPoint,
)
from models.paper_trading import (
    JournalEntry,
    OrderAction,
    PaperEquityPoint,
    PaperPerformance,
    PaperStatistics,
    PaperTradingReport,
)
from models.recommendation import (
    Direction,
    RecommendationReport,
    RecommendationResult,
    RecommendationStrength,
    SuggestedAction,
)
from tests.helpers import make_simulated_trade

_T0 = datetime(2024, 1, 1, tzinfo=UTC)


def make_recommendation_result(
    rec_id: str = "rec:1",
    direction: Direction = Direction.LONG,
    strength: RecommendationStrength = RecommendationStrength.HIGH,
    confidence: float = 0.72,
    rating: float = 68.0,
    risk_factor: float = 30.0,
    reasons: list[str] | None = None,
    warnings: list[str] | None = None,
) -> RecommendationResult:
    """Baut eine einzelne :class:`RecommendationResult` mit Risiko-Faktor."""
    return RecommendationResult(
        recommendation_id=rec_id,
        risk_id="risk:1",
        score_id="score:1",
        hypothesis_id="h1",
        direction=direction,
        recommendation_strength=strength,
        confidence=confidence,
        overall_rating=rating,
        suggested_action=SuggestedAction.OPEN,
        reasons=reasons if reasons is not None else ["Trend intakt", "Score hoch"],
        warnings=warnings if warnings is not None else ["Spread erhöht"],
        summary=f"{direction.value.upper()} {strength.value}",
        metadata={"factors": {"risk": risk_factor, "score": rating}},
        timestamp=_T0,
    )


def make_recommendation_report(
    symbol: str = "AAPL", results: list[RecommendationResult] | None = None
) -> RecommendationReport:
    """Baut einen :class:`RecommendationReport` mit zwei Empfehlungen."""
    if results is None:
        results = [
            make_recommendation_result("rec:1", Direction.LONG, RecommendationStrength.HIGH),
            make_recommendation_result(
                "rec:2", Direction.SHORT, RecommendationStrength.MEDIUM, rating=54.0
            ),
        ]
    return RecommendationReport(results=results, valid=True, metadata={"symbol": symbol})


def make_paper_report(points: int = 4, journal_entries: int = 2) -> PaperTradingReport:
    """Baut einen :class:`PaperTradingReport` mit Kurve, Statistik und Journal."""
    curve = [
        PaperEquityPoint(
            timestamp=_T0 + timedelta(days=i),
            equity=10_000.0 + i * 120.0,
            drawdown_pct=float(i % 2),
            exposure_pct=20.0,
            open_positions=1,
        )
        for i in range(points)
    ]
    performance = PaperPerformance(
        current_equity=10_000.0 + (points - 1) * 120.0,
        running_drawdown_pct=1.5,
        portfolio_exposure_pct=20.0,
        realized_pnl=360.0,
        unrealized_pnl=90.0,
        equity_curve=curve,
    )
    statistics = PaperStatistics(
        win_rate=0.6,
        profit_factor=1.8,
        current_equity=performance.current_equity,
        open_positions=1,
        closed_positions=5,
    )
    journal = [
        JournalEntry(
            entry_id=f"j:{i}",
            position_id="pos:1",
            recommendation_id="rec:1",
            action=OrderAction.OPEN if i % 2 == 0 else OrderAction.CLOSE,
            direction=Direction.LONG,
            recommendation_strength=RecommendationStrength.HIGH,
            entry_price=100.0,
            exit_price=105.0 if i % 2 else 0.0,
            reason="Take-Profit" if i % 2 else "Einstieg",
            pnl=50.0 if i % 2 else 0.0,
            reasons=["Trend"],
            warnings=[],
            timestamp=_T0 + timedelta(days=i),
        )
        for i in range(journal_entries)
    ]
    return PaperTradingReport(
        statistics=statistics,
        performance=performance,
        journal=journal,
        valid=True,
        metadata={"symbol": "AAPL"},
    )


def make_backtest_result(trades: int = 3) -> BacktestResult:
    """Baut ein einzelnes :class:`BacktestResult` mit Trades, Kurve und Benchmark."""
    trade_list = [
        make_simulated_trade(trade_id=f"bt:AAPL:{i}", profit=(50.0 if i % 2 == 0 else -30.0))
        for i in range(trades)
    ]
    curve = [
        EquityPoint(
            timestamp=_T0 + timedelta(days=i),
            equity=10_000.0 + i * 80.0,
            drawdown=float(i),
            drawdown_pct=float(i % 3),
        )
        for i in range(trades)
    ]
    benchmark = BenchmarkResult(
        name="buy_and_hold",
        start_price=100.0,
        end_price=112.0,
        start_equity=10_000.0,
        end_equity=11_200.0,
        return_pct=12.0,
    )
    return BacktestResult(
        backtest_id="bt:AAPL",
        symbol="AAPL",
        timeframe="base",
        start_date=_T0,
        end_date=_T0 + timedelta(days=trades),
        signal_count=trades,
        trade_count=trades,
        win_rate=0.66,
        loss_rate=0.34,
        profit_factor=1.9,
        average_win=50.0,
        average_loss=-30.0,
        average_risk_reward=2.0,
        average_holding_time=3.0,
        maximum_drawdown=8.0,
        expectancy=20.0,
        sharpe_ratio=1.2,
        sortino_ratio=1.4,
        calmar_ratio=0.9,
        total_return=240.0,
        total_return_pct=2.4,
        final_equity=10_240.0,
        equity_curve=curve,
        trades=trade_list,
        benchmark=benchmark,
        valid=True,
        summary="Backtest ok",
    )


def make_backtest_report(trades: int = 3) -> BacktestReport:
    """Baut einen :class:`BacktestReport` mit einem Ergebnis."""
    return BacktestReport(results=[make_backtest_result(trades)], valid=True)


def _group(label: str, count: int = 4, win_rate: float = 0.5) -> GroupStatistics:
    """Baut eine :class:`GroupStatistics` mit plausiblen Werten."""
    return GroupStatistics(
        label=label,
        trade_count=count,
        win_rate=win_rate,
        loss_rate=1.0 - win_rate,
        profit_factor=1.5,
        average_winner=60.0,
        average_loser=-40.0,
        average_return=15.0,
        average_holding_time=2.5,
        maximum_drawdown=6.0,
        total_pnl=count * 15.0,
    )


def make_analytics_result() -> AnalyticsResult:
    """Baut ein :class:`AnalyticsResult` mit gefüllten Gruppen-Statistiken."""
    return AnalyticsResult(
        analytics_id="an:1",
        backtest_id="bt:AAPL",
        paper_trading_id="pt:AAPL",
        trade_count=8,
        win_rate=0.55,
        loss_rate=0.45,
        profit_factor=1.7,
        expectancy=18.0,
        average_winner=60.0,
        average_loser=-40.0,
        maximum_drawdown=7.0,
        average_holding_time=2.5,
        average_risk_reward=2.0,
        long_statistics=_group("long", 5, 0.6),
        short_statistics=_group("short", 3, 0.4),
        strategy_statistics={"trend_following": _group("trend_following")},
        pattern_statistics={"fvg": _group("fvg")},
        recommendation_statistics={"high": _group("high")},
        risk_statistics={"low": _group("low")},
        market_statistics={"trend": _group("trend")},
        time_statistics={
            "weekday": {"Mon": _group("Mon")},
            "holding": {"1-3": _group("1-3")},
        },
        journal_statistics={
            "total_entries": 6,
            "closed_entries": 4,
            "winners": 3,
            "losers": 1,
            "realized_pnl": 120.0,
        },
        summary="Analyse abgeschlossen.",
    )


def make_analytics_report() -> AnalyticsReport:
    """Baut einen :class:`AnalyticsReport`."""
    return AnalyticsReport(result=make_analytics_result(), valid=True)
