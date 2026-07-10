"""Handelsstatistik des simulierten Portfolios.

Reine Funktionen über abgeschlossene Trades und die Positionszählung. Ergebnis
ist eine unveränderliche :class:`~models.paper_trading.PaperStatistics`.
Konventionen wie im Backtesting: ohne Trades neutral (``0.0``), ``average_loser``
negativ, ``profit_factor`` ``inf`` ohne Verluste.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from models.paper_trading import PaperStatistics, PaperTrade


def win_rate(trades: Sequence[PaperTrade]) -> float:
    """Trefferquote 0..1."""
    if not trades:
        return 0.0
    return sum(1 for t in trades if t.is_win) / len(trades)


def loss_rate(trades: Sequence[PaperTrade]) -> float:
    """Verlustquote 0..1."""
    if not trades:
        return 0.0
    return sum(1 for t in trades if t.is_loss) / len(trades)


def profit_factor(trades: Sequence[PaperTrade]) -> float:
    """Bruttogewinn / Bruttoverlust (``inf`` ohne Verluste, ``0`` ohne Trades)."""
    if not trades:
        return 0.0
    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = sum(-t.pnl for t in trades if t.pnl < 0)
    if gross_loss == 0.0:
        return math.inf if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def average_winner(trades: Sequence[PaperTrade]) -> float:
    """Durchschnittlicher Gewinn der Gewinner-Trades (≥ 0)."""
    wins = [t.pnl for t in trades if t.is_win]
    return sum(wins) / len(wins) if wins else 0.0


def average_loser(trades: Sequence[PaperTrade]) -> float:
    """Durchschnittlicher Verlust der Verlierer-Trades (≤ 0)."""
    losses = [t.pnl for t in trades if t.is_loss]
    return sum(losses) / len(losses) if losses else 0.0


def average_holding_time(trades: Sequence[PaperTrade]) -> float:
    """Durchschnittliche Haltedauer in Tagen (nur Trades mit Zeitangabe)."""
    days = [t.holding_time.total_seconds() / 86400.0 for t in trades if t.holding_time is not None]
    return sum(days) / len(days) if days else 0.0


def compute_statistics(
    trades: Sequence[PaperTrade],
    open_positions: int,
    closed_positions: int,
    current_equity: float,
    starting_capital: float,
) -> PaperStatistics:
    """Baut eine :class:`PaperStatistics` aus Trades und Positionszählung."""
    portfolio_return = (
        (current_equity - starting_capital) / starting_capital * 100.0
        if starting_capital > 0
        else 0.0
    )
    return PaperStatistics(
        win_rate=win_rate(trades),
        loss_rate=loss_rate(trades),
        profit_factor=profit_factor(trades),
        average_winner=average_winner(trades),
        average_loser=average_loser(trades),
        average_holding_time=average_holding_time(trades),
        current_equity=current_equity,
        portfolio_return_pct=portfolio_return,
        open_positions=open_positions,
        closed_positions=closed_positions,
    )
