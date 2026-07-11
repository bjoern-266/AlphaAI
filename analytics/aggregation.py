"""Reine, wiederverwendbare Kennzahl-Bausteine für die Analyse.

Alle Funktionen sind **rein** (ohne Seiteneffekt) und arbeiten auf einer Sequenz
von :class:`~models.analytics.AnalyticsTrade`. Sie sind die einzige Quelle der
Kennzahl-Definitionen; jedes Analysemodell nutzt ausschließlich diese Bausteine,
damit alle Statistiken **reproduzierbar** und einheitlich sind (keine Blackbox).

Konventionen (wie im Backtesting/Paper Trading): ohne Trades neutral (``0.0``),
``average_loser`` negativ, ``profit_factor`` ``inf`` ohne Verluste. Der
Drawdown wird auf einer Kapitalkurve ``base_capital + kumulierter PnL`` gemessen
und als Prozent des Peaks angegeben (``base_capital`` aus der Konfiguration).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence

from models.analytics import AnalyticsTrade, GroupStatistics

DEFAULT_BASE_CAPITAL = 10000.0


def total_pnl(trades: Sequence[AnalyticsTrade]) -> float:
    """Summe aller Ergebnisse (Kontowährung)."""
    return float(sum(t.pnl for t in trades))


def win_rate(trades: Sequence[AnalyticsTrade]) -> float:
    """Trefferquote 0..1."""
    if not trades:
        return 0.0
    return sum(1 for t in trades if t.is_win) / len(trades)


def loss_rate(trades: Sequence[AnalyticsTrade]) -> float:
    """Verlustquote 0..1."""
    if not trades:
        return 0.0
    return sum(1 for t in trades if t.is_loss) / len(trades)


def profit_factor(trades: Sequence[AnalyticsTrade]) -> float:
    """Bruttogewinn / Bruttoverlust (``inf`` ohne Verluste, ``0`` ohne Trades)."""
    if not trades:
        return 0.0
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = sum(-t.pnl for t in trades if t.pnl < 0)
    if gross_loss == 0.0:
        return math.inf if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def average_winner(trades: Sequence[AnalyticsTrade]) -> float:
    """Durchschnittlicher Gewinn der Gewinner-Trades (≥ 0)."""
    wins = [t.pnl for t in trades if t.is_win]
    return sum(wins) / len(wins) if wins else 0.0


def average_loser(trades: Sequence[AnalyticsTrade]) -> float:
    """Durchschnittlicher Verlust der Verlierer-Trades (≤ 0)."""
    losses = [t.pnl for t in trades if t.is_loss]
    return sum(losses) / len(losses) if losses else 0.0


def average_return(trades: Sequence[AnalyticsTrade]) -> float:
    """Durchschnittliches Ergebnis je Trade (Kontowährung)."""
    if not trades:
        return 0.0
    return total_pnl(trades) / len(trades)


def expectancy(trades: Sequence[AnalyticsTrade]) -> float:
    """Erwartungswert je Trade (= durchschnittliches Ergebnis)."""
    return average_return(trades)


def average_holding_days(trades: Sequence[AnalyticsTrade]) -> float:
    """Durchschnittliche Haltedauer in Tagen (nur Trades mit Zeitangabe)."""
    days = [t.holding_days for t in trades if t.holding_days > 0]
    return sum(days) / len(days) if days else 0.0


def average_risk_reward(trades: Sequence[AnalyticsTrade]) -> float:
    """Durchschnittliches Chance-Risiko-Verhältnis (nur Trades mit Angabe)."""
    values = [t.risk_reward for t in trades if t.risk_reward > 0]
    return sum(values) / len(values) if values else 0.0


def _sort_key(trade: AnalyticsTrade) -> tuple[int, float]:
    """Sortiert Trades chronologisch (Ausstieg, Fallback stabil)."""
    exit_time = trade.exit_time
    if exit_time is not None:
        return (0, exit_time.timestamp())
    return (1, 0.0)


def chronological(trades: Sequence[AnalyticsTrade]) -> list[AnalyticsTrade]:
    """Gibt die Trades chronologisch (nach Ausstieg) sortiert zurück."""
    return sorted(trades, key=_sort_key)


def maximum_drawdown_pct(
    trades: Sequence[AnalyticsTrade], base_capital: float = DEFAULT_BASE_CAPITAL
) -> float:
    """Maximaler Drawdown der Kapitalkurve in Prozent (0..100).

    Die Kapitalkurve ist ``base_capital`` plus kumulierter PnL (chronologisch).
    """
    if not trades or base_capital <= 0:
        return 0.0
    equity = base_capital
    peak = base_capital
    max_dd = 0.0
    for trade in sorted(trades, key=_sort_key):
        equity += trade.pnl
        peak = max(peak, equity)
        if peak > 0:
            max_dd = max(max_dd, (peak - equity) / peak * 100.0)
    return max_dd


def group_by(
    trades: Sequence[AnalyticsTrade], key: Callable[[AnalyticsTrade], str]
) -> dict[str, list[AnalyticsTrade]]:
    """Gruppiert Trades nach einem Label (Reihenfolge des ersten Auftretens)."""
    groups: dict[str, list[AnalyticsTrade]] = {}
    for trade in trades:
        groups.setdefault(key(trade), []).append(trade)
    return groups


def group_statistics(
    label: str, trades: Sequence[AnalyticsTrade], base_capital: float = DEFAULT_BASE_CAPITAL
) -> GroupStatistics:
    """Baut die :class:`GroupStatistics` einer Trade-Gruppe."""
    return GroupStatistics(
        label=label,
        trade_count=len(trades),
        win_rate=win_rate(trades),
        loss_rate=loss_rate(trades),
        profit_factor=profit_factor(trades),
        average_winner=average_winner(trades),
        average_loser=average_loser(trades),
        average_return=average_return(trades),
        average_holding_time=average_holding_days(trades),
        maximum_drawdown=maximum_drawdown_pct(trades, base_capital),
        total_pnl=total_pnl(trades),
    )


def grouped_statistics(
    trades: Sequence[AnalyticsTrade],
    key: Callable[[AnalyticsTrade], str],
    base_capital: float = DEFAULT_BASE_CAPITAL,
) -> dict[str, GroupStatistics]:
    """Gruppiert Trades und liefert je Gruppe eine :class:`GroupStatistics`."""
    return {
        label: group_statistics(label, group, base_capital)
        for label, group in group_by(trades, key).items()
    }
