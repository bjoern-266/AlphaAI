"""Kapital-, Drawdown- und Exposure-Kennzahlen des simulierten Portfolios.

Reine Funktion, die aus den (bereits ermittelten) Portfolio-Größen eine
unveränderliche :class:`~models.paper_trading.PaperPerformance` baut. Keine
Handelsregel, kein Zustand.
"""

from __future__ import annotations

from collections.abc import Sequence

from models.paper_trading import PaperEquityPoint, PaperPerformance


def compute_performance(
    starting_capital: float,
    current_equity: float,
    realized_pnl: float,
    unrealized_pnl: float,
    running_drawdown_pct: float,
    maximum_drawdown_pct: float,
    exposure_pct: float,
    equity_curve: Sequence[PaperEquityPoint],
) -> PaperPerformance:
    """Baut eine :class:`PaperPerformance` aus den Portfolio-Größen."""
    portfolio_return = (
        (current_equity - starting_capital) / starting_capital * 100.0
        if starting_capital > 0
        else 0.0
    )
    return PaperPerformance(
        starting_capital=starting_capital,
        current_equity=current_equity,
        portfolio_return_pct=portfolio_return,
        running_drawdown_pct=running_drawdown_pct,
        maximum_drawdown_pct=maximum_drawdown_pct,
        portfolio_exposure_pct=exposure_pct,
        realized_pnl=realized_pnl,
        unrealized_pnl=unrealized_pnl,
        equity_curve=list(equity_curve),
    )
