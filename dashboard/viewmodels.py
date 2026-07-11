"""View Models – lesen bestehende Reports in anzeigefertige Strukturen.

Die :class:`DashboardViewModel` bündelt für jede Seite die **bereits
vorhandenen** Werte aus den Reports. Es findet **keine** Berechnung, **keine**
Ableitung neuer Kennzahlen und **keine** Veränderung von Daten statt – nur
Ablesen. Fehlt ein Wert im Report, bleibt er ``None`` (die Widgets zeigen dann
einen Platzhalter, es wird **nichts** ersatzweise berechnet).

Alle View-Model-Typen sind unveränderlich (`frozen`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dashboard.state import SystemStatus
from dashboard.status import module_status, status_item
from models.analytics import AnalyticsReport, GroupStatistics
from models.backtest import BacktestReport
from models.dashboard import StatusItem
from models.indicator import IndicatorResult
from models.paper_trading import PaperTradingReport
from models.pattern import PatternReport
from models.recommendation import RecommendationReport, RecommendationResult
from models.risk import RiskReport
from models.score import ScoreReport
from models.strategy import StrategyReport


@dataclass(frozen=True, slots=True)
class ReportBundle:
    """Sammlung der (optionalen) bestehenden Reports als Dashboard-Eingabe.

    Alle Felder sind optional; fehlt ein Report, gilt das Modul als „offline".
    """

    analytics: AnalyticsReport | None = None
    paper_trading: PaperTradingReport | None = None
    backtest: BacktestReport | None = None
    recommendation: RecommendationReport | None = None
    risk: RiskReport | None = None
    score: ScoreReport | None = None
    strategy: StrategyReport | None = None
    pattern: PatternReport | None = None
    indicator: IndicatorResult | None = None


# --------------------------------------------------------------------------- #
# Zeilen-Typen (rohe, abgelesene Werte)                                       #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class LiveRow:
    """Eine Zeile der Live-Analyse (Werte aus der Empfehlung)."""

    symbol: str
    direction: str
    strength: str
    confidence: float | None
    score: float | None
    risk: float | None
    pattern: str
    strategy: str
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RecommendationRow:
    """Eine Empfehlungszeile (Werte aus dem Recommendation-Report)."""

    symbol: str
    direction: str
    strength: str
    confidence: float | None
    score: float | None
    risk: float | None
    summary: str


@dataclass(frozen=True, slots=True)
class JournalRow:
    """Eine Journalzeile (Werte aus dem Paper-Trading-Journal)."""

    timestamp: str
    action: str
    direction: str
    strength: str
    entry_price: float | None
    exit_price: float | None
    pnl: float | None
    reason: str
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TradeRow:
    """Eine Backtest-Trade-Zeile (Werte aus dem Backtest-Report)."""

    symbol: str
    direction: str
    strength: str
    entry_price: float | None
    exit_price: float | None
    pnl: float | None
    outcome: str
    exit_reason: str


# --------------------------------------------------------------------------- #
# Seiten-View-Models                                                          #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class OverviewVM:
    """Kennzahlen der Übersichtsseite (abgelesen)."""

    portfolio_value: float | None = None
    current_equity: float | None = None
    todays_pnl: float | None = None
    current_drawdown: float | None = None
    open_positions: int | None = None
    closed_positions: int | None = None
    profit_factor: float | None = None
    win_rate: float | None = None
    recommendation_count: int | None = None
    statuses: tuple[StatusItem, ...] = ()


@dataclass(frozen=True, slots=True)
class PortfolioVM:
    """Kennzahlen der Paper-Portfolio-Seite (abgelesen)."""

    portfolio_value: float | None = None
    cash: float | None = None
    exposure: float | None = None
    open_positions: int | None = None
    closed_positions: int | None = None
    current_equity: float | None = None
    realized_pnl: float | None = None
    unrealized_pnl: float | None = None
    todays_pnl: float | None = None
    equity_curve: tuple[float, ...] = ()
    equity_labels: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BacktestVM:
    """Kennzahlen der Backtest-Seite (abgelesen)."""

    profit_factor: float | None = None
    max_drawdown: float | None = None
    win_rate: float | None = None
    benchmark_name: str = ""
    benchmark_return: float | None = None
    total_return_pct: float | None = None
    equity_curve: tuple[float, ...] = ()
    equity_labels: tuple[str, ...] = ()
    trades: tuple[TradeRow, ...] = ()


@dataclass(frozen=True, slots=True)
class LiveVM:
    """Watchlist der Live-Analyse (abgelesen)."""

    symbol: str = ""
    rows: tuple[LiveRow, ...] = ()


@dataclass(frozen=True, slots=True)
class AnalyticsVM:
    """Kennzahlen der Analytics-Seite (direkt aus dem AnalyticsResult)."""

    trade_count: int | None = None
    win_rate: float | None = None
    loss_rate: float | None = None
    profit_factor: float | None = None
    expectancy: float | None = None
    long_statistics: GroupStatistics | None = None
    short_statistics: GroupStatistics | None = None
    strategy_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    pattern_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    recommendation_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    risk_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    market_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    time_statistics: dict[str, dict[str, GroupStatistics]] = field(default_factory=dict)
    journal_statistics: dict = field(default_factory=dict)
    summary: str = ""


@dataclass(frozen=True, slots=True)
class PerformanceVM:
    """Kennzahlen der Performance-Seite (abgelesen)."""

    equity_curve: tuple[float, ...] = ()
    equity_labels: tuple[str, ...] = ()
    drawdown_curve: tuple[float, ...] = ()
    profit_distribution: tuple[float, ...] = ()
    holding_labels: tuple[str, ...] = ()
    holding_counts: tuple[float, ...] = ()


@dataclass(frozen=True, slots=True)
class JournalVM:
    """Zeilen der Trade-Journal-Seite (abgelesen)."""

    rows: tuple[JournalRow, ...] = ()


@dataclass(frozen=True, slots=True)
class RecommendationsVM:
    """Zeilen der Empfehlungsseite (abgelesen)."""

    symbol: str = ""
    rows: tuple[RecommendationRow, ...] = ()


@dataclass(frozen=True, slots=True)
class DashboardViewModel:
    """Bündelt alle Seiten-View-Models (unveränderlich)."""

    overview: OverviewVM = field(default_factory=OverviewVM)
    portfolio: PortfolioVM = field(default_factory=PortfolioVM)
    backtest: BacktestVM = field(default_factory=BacktestVM)
    live: LiveVM = field(default_factory=LiveVM)
    analytics: AnalyticsVM = field(default_factory=AnalyticsVM)
    performance: PerformanceVM = field(default_factory=PerformanceVM)
    journal: JournalVM = field(default_factory=JournalVM)
    recommendations: RecommendationsVM = field(default_factory=RecommendationsVM)


# --------------------------------------------------------------------------- #
# Ablesen der Reports                                                         #
# --------------------------------------------------------------------------- #


def _factor(result: RecommendationResult, name: str) -> float | None:
    """Liest einen Empfehlungs-Faktor (0..100) aus den Metadaten oder ``None``."""
    factors = result.metadata.get("factors", {}) if isinstance(result.metadata, dict) else {}
    value = factors.get(name)
    return float(value) if isinstance(value, (int, float)) else None


def _system_statuses(bundle: ReportBundle) -> tuple[StatusItem, ...]:
    """Leitet die System-Status-Anzeige aus dem Vorhandensein der Reports ab."""
    return (
        status_item("Market Data", module_status(bundle.indicator is not None)),
        status_item(
            "Recommendation Engine",
            module_status(
                bundle.recommendation is not None,
                valid=getattr(bundle.recommendation, "valid", True),
                has_data=bool(getattr(bundle.recommendation, "results", [])),
            ),
        ),
        status_item(
            "Paper Trading",
            module_status(
                bundle.paper_trading is not None,
                valid=getattr(bundle.paper_trading, "valid", True),
            ),
        ),
        status_item(
            "Backtesting",
            module_status(
                bundle.backtest is not None, valid=getattr(bundle.backtest, "valid", True)
            ),
        ),
        status_item(
            "Analytics",
            module_status(
                bundle.analytics is not None, valid=getattr(bundle.analytics, "valid", True)
            ),
        ),
    )


def _overview(bundle: ReportBundle) -> OverviewVM:
    """Liest die Übersichts-Kennzahlen (nur Ablesen)."""
    perf = getattr(bundle.paper_trading, "performance", None)
    stats = getattr(bundle.paper_trading, "statistics", None)
    result = getattr(bundle.analytics, "result", None)
    return OverviewVM(
        portfolio_value=getattr(perf, "current_equity", None),
        current_equity=getattr(perf, "current_equity", None),
        todays_pnl=None,  # Nicht in den Reports gespeichert – Platzhalter.
        current_drawdown=getattr(perf, "running_drawdown_pct", None),
        open_positions=getattr(stats, "open_positions", None),
        closed_positions=getattr(stats, "closed_positions", None),
        profit_factor=getattr(result, "profit_factor", getattr(stats, "profit_factor", None)),
        win_rate=getattr(result, "win_rate", getattr(stats, "win_rate", None)),
        recommendation_count=getattr(bundle.recommendation, "recommendation_count", None),
        statuses=_system_statuses(bundle),
    )


def _portfolio(bundle: ReportBundle) -> PortfolioVM:
    """Liest die Paper-Portfolio-Kennzahlen (nur Ablesen)."""
    perf = getattr(bundle.paper_trading, "performance", None)
    stats = getattr(bundle.paper_trading, "statistics", None)
    curve = getattr(perf, "equity_curve", []) or []
    return PortfolioVM(
        portfolio_value=getattr(perf, "current_equity", None),
        cash=None,  # Nicht als Einzelwert gespeichert – Platzhalter.
        exposure=getattr(perf, "portfolio_exposure_pct", None),
        open_positions=getattr(stats, "open_positions", None),
        closed_positions=getattr(stats, "closed_positions", None),
        current_equity=getattr(perf, "current_equity", None),
        realized_pnl=getattr(perf, "realized_pnl", None),
        unrealized_pnl=getattr(perf, "unrealized_pnl", None),
        todays_pnl=None,
        equity_curve=tuple(float(p.equity) for p in curve),
        equity_labels=tuple(_ts(p.timestamp) for p in curve),
    )


def _backtest(bundle: ReportBundle) -> BacktestVM:
    """Liest die Backtest-Kennzahlen aus dem ersten Ergebnis (nur Ablesen)."""
    results = getattr(bundle.backtest, "results", []) or []
    if not results:
        return BacktestVM()
    result = results[0]
    benchmark = getattr(result, "benchmark", None)
    curve = getattr(result, "equity_curve", []) or []
    trades = tuple(
        TradeRow(
            symbol=t.symbol,
            direction=t.direction.value,
            strength=t.recommendation_strength.value,
            entry_price=t.entry_price,
            exit_price=t.exit_price,
            pnl=t.profit,
            outcome=t.outcome.value,
            exit_reason=t.exit_reason.value,
        )
        for t in getattr(result, "trades", []) or []
    )
    return BacktestVM(
        profit_factor=result.profit_factor,
        max_drawdown=result.maximum_drawdown,
        win_rate=result.win_rate,
        benchmark_name=getattr(benchmark, "name", ""),
        benchmark_return=getattr(benchmark, "return_pct", None),
        total_return_pct=result.total_return_pct,
        equity_curve=tuple(float(p.equity) for p in curve),
        equity_labels=tuple(_ts(p.timestamp) for p in curve),
        trades=trades,
    )


def _live(bundle: ReportBundle) -> LiveVM:
    """Liest die Watchlist aus dem Recommendation-Report (nur Ablesen)."""
    report = bundle.recommendation
    if report is None:
        return LiveVM()
    symbol = str(report.metadata.get("symbol", "")) if isinstance(report.metadata, dict) else ""
    rows = tuple(
        LiveRow(
            symbol=symbol,
            direction=r.direction.value,
            strength=r.recommendation_strength.value,
            confidence=r.confidence,
            score=r.overall_rating,
            risk=_factor(r, "risk"),
            pattern="—",
            strategy="—",
            reasons=tuple(r.reasons),
            warnings=tuple(r.warnings),
        )
        for r in report.results
    )
    return LiveVM(symbol=symbol, rows=rows)


def _analytics(bundle: ReportBundle) -> AnalyticsVM:
    """Übernimmt die bereits berechneten Analytics-Kennzahlen (nur Ablesen)."""
    result = getattr(bundle.analytics, "result", None)
    if result is None:
        return AnalyticsVM()
    return AnalyticsVM(
        trade_count=result.trade_count,
        win_rate=result.win_rate,
        loss_rate=result.loss_rate,
        profit_factor=result.profit_factor,
        expectancy=result.expectancy,
        long_statistics=result.long_statistics,
        short_statistics=result.short_statistics,
        strategy_statistics=dict(result.strategy_statistics),
        pattern_statistics=dict(result.pattern_statistics),
        recommendation_statistics=dict(result.recommendation_statistics),
        risk_statistics=dict(result.risk_statistics),
        market_statistics=dict(result.market_statistics),
        time_statistics=dict(result.time_statistics),
        journal_statistics=dict(result.journal_statistics),
        summary=result.summary,
    )


def _performance(bundle: ReportBundle) -> PerformanceVM:
    """Liest Performance-Kurven/-Verteilungen aus den Reports (nur Ablesen)."""
    perf = getattr(bundle.paper_trading, "performance", None)
    curve = getattr(perf, "equity_curve", []) or []
    profits: tuple[float, ...] = ()
    results = getattr(bundle.backtest, "results", []) or []
    if results:
        profits = tuple(float(t.profit) for t in getattr(results[0], "trades", []) or [])
    holding = {}
    result = getattr(bundle.analytics, "result", None)
    if result is not None:
        holding = result.time_statistics.get("holding", {})
    return PerformanceVM(
        equity_curve=tuple(float(p.equity) for p in curve),
        equity_labels=tuple(_ts(p.timestamp) for p in curve),
        drawdown_curve=tuple(float(p.drawdown_pct) for p in curve),
        profit_distribution=profits,
        holding_labels=tuple(holding.keys()),
        holding_counts=tuple(float(g.trade_count) for g in holding.values()),
    )


def _journal(bundle: ReportBundle) -> JournalVM:
    """Liest die Journalzeilen aus dem Paper-Trading-Journal (nur Ablesen)."""
    entries = getattr(bundle.paper_trading, "journal", []) or []
    rows = tuple(
        JournalRow(
            timestamp=_ts(e.timestamp),
            action=e.action.value,
            direction=e.direction.value,
            strength=e.recommendation_strength.value,
            entry_price=e.entry_price,
            exit_price=e.exit_price,
            pnl=e.pnl,
            reason=e.reason,
            reasons=tuple(e.reasons),
            warnings=tuple(e.warnings),
        )
        for e in entries
    )
    return JournalVM(rows=rows)


def _recommendations(bundle: ReportBundle) -> RecommendationsVM:
    """Liest die aktuellen Empfehlungen (nur Ablesen)."""
    report = bundle.recommendation
    if report is None:
        return RecommendationsVM()
    symbol = str(report.metadata.get("symbol", "")) if isinstance(report.metadata, dict) else ""
    rows = tuple(
        RecommendationRow(
            symbol=symbol,
            direction=r.direction.value,
            strength=r.recommendation_strength.value,
            confidence=r.confidence,
            score=r.overall_rating,
            risk=_factor(r, "risk"),
            summary=r.summary,
        )
        for r in report.results
    )
    return RecommendationsVM(symbol=symbol, rows=rows)


def build_view_model(bundle: ReportBundle) -> DashboardViewModel:
    """Baut das gesamte :class:`DashboardViewModel` aus dem Report-Bundle."""
    return DashboardViewModel(
        overview=_overview(bundle),
        portfolio=_portfolio(bundle),
        backtest=_backtest(bundle),
        live=_live(bundle),
        analytics=_analytics(bundle),
        performance=_performance(bundle),
        journal=_journal(bundle),
        recommendations=_recommendations(bundle),
    )


def _ts(value: object) -> str:
    """Formatiert einen Zeitstempel als Text (leer, wenn nicht vorhanden)."""
    if value is None:
        return ""
    try:
        return value.strftime("%Y-%m-%d")  # type: ignore[attr-defined]
    except AttributeError:
        return str(value)


# Statusklasse für die Wiederverwendung in Widgets/Tests re-exportiert.
__all__ = [
    "ReportBundle",
    "DashboardViewModel",
    "OverviewVM",
    "PortfolioVM",
    "BacktestVM",
    "LiveVM",
    "AnalyticsVM",
    "PerformanceVM",
    "JournalVM",
    "RecommendationsVM",
    "LiveRow",
    "RecommendationRow",
    "JournalRow",
    "TradeRow",
    "build_view_model",
    "SystemStatus",
]
