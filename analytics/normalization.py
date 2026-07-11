"""Normalisierung bestehender Trades in :class:`AnalyticsTrade`.

Reine, seiteneffektfreie Funktionen. Sie **lesen** die bestehenden Ergebnisse aus
Backtesting und Paper Trading und überführen sie in den einheitlichen
Analyse-Trade – **ohne** die Quelldaten zu verändern. Abgeleitete Dimensionen
(Strategie, Risiko-Level, Score) stammen ausschließlich aus ``recommendation_id``
und ``reasons`` (siehe :mod:`analytics.labeling`) und sind damit vollständig
nachvollziehbar.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from analytics.labeling import classify_outcome, parse_risk_level, parse_score, parse_strategy
from models.analytics import AnalyticsTrade
from models.backtest import BacktestReport, SimulatedTrade
from models.paper_trading import PaperTradingReport, PaperTradingResult

# Label-Schlüssel, die – falls in der Trade-Metadata vorhanden – als
# Analyse-Dimensionen übernommen werden (erweiterbar ohne Engine-Änderung).
_LABEL_KEYS = ("pattern", "market_phase", "volatility", "liquidity")


def _labels(metadata: dict) -> dict[str, str]:
    """Übernimmt bekannte Dimensions-Labels aus der Metadata (falls vorhanden)."""
    return {key: str(metadata[key]) for key in _LABEL_KEYS if key in metadata}


def _holding_days(holding_time: timedelta | None) -> float:
    """Haltedauer in Tagen aus einer Zeitspanne (0.0, falls unbekannt)."""
    return holding_time.total_seconds() / 86400.0 if holding_time is not None else 0.0


def from_backtest_trade(trade: SimulatedTrade) -> AnalyticsTrade:
    """Normalisiert einen Backtest-Trade."""
    return AnalyticsTrade(
        source="backtest",
        trade_id=trade.trade_id,
        symbol=trade.symbol,
        recommendation_id=trade.recommendation_id,
        direction=trade.direction,
        recommendation_strength=trade.recommendation_strength,
        strategy=parse_strategy(trade.recommendation_id),
        risk_level=parse_risk_level(trade.reasons),
        score=parse_score(trade.reasons),
        pnl=trade.profit,
        pnl_pct=trade.profit_pct,
        return_on_risk=trade.return_on_risk,
        risk_reward=trade.risk_reward,
        holding_time=trade.holding_time,
        holding_days=_holding_days(trade.holding_time),
        entry_time=trade.entry_time,
        exit_time=trade.exit_time,
        close_reason=trade.exit_reason.value,
        outcome=trade.outcome.value,
        labels=_labels(trade.metadata),
        reasons=list(trade.reasons),
        warnings=list(trade.warnings),
        metadata=dict(trade.metadata),
    )


def from_paper_result(result: PaperTradingResult) -> AnalyticsTrade:
    """Normalisiert ein geschlossenes Paper-Trading-Ergebnis."""
    holding_time = None
    if isinstance(result.entry_time, datetime) and isinstance(result.exit_time, datetime):
        holding_time = result.exit_time - result.entry_time
    return AnalyticsTrade(
        source="paper_trading",
        trade_id=result.paper_trading_id,
        symbol=result.symbol,
        recommendation_id=result.recommendation_id,
        direction=result.direction,
        recommendation_strength=result.recommendation_strength,
        strategy=parse_strategy(result.recommendation_id),
        risk_level=parse_risk_level(result.reasons),
        score=parse_score(result.reasons),
        pnl=result.pnl,
        pnl_pct=result.pnl_pct,
        return_on_risk=0.0,
        risk_reward=0.0,
        holding_time=holding_time,
        holding_days=_holding_days(holding_time),
        entry_time=result.entry_time,
        exit_time=result.exit_time,
        close_reason=result.close_reason.value if result.close_reason else "",
        outcome=classify_outcome(result.pnl),
        labels=_labels(result.metadata),
        reasons=list(result.reasons),
        warnings=list(result.warnings),
        metadata=dict(result.metadata),
    )


def normalize(
    backtest_report: BacktestReport | None, paper_report: PaperTradingReport | None
) -> list[AnalyticsTrade]:
    """Baut die Liste normalisierter Trades aus beiden Reports (nur Lesen)."""
    trades: list[AnalyticsTrade] = []
    if backtest_report is not None:
        for result in backtest_report.results:
            trades.extend(from_backtest_trade(t) for t in result.trades)
    if paper_report is not None:
        trades.extend(from_paper_result(r) for r in paper_report.closed_results)
    return trades
