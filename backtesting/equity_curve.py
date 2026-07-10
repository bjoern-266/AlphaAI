"""Kapitalkurve und Drawdown aus simulierten Trades.

Reine, seiteneffektfreie Funktionen. Die Kapitalkurve beginnt beim Startkapital
und wird nach jedem abgeschlossenen Trade fortgeschrieben. Der Drawdown misst
den Rückgang vom bisherigen Kapital-Hoch (Peak).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from models.backtest import EquityPoint, SimulatedTrade


def _sort_key(trade: SimulatedTrade) -> tuple[int, float]:
    """Sortiert Trades chronologisch nach Ausstieg (Fallback: stabil)."""
    exit_time = trade.exit_time
    if isinstance(exit_time, datetime):
        return (0, exit_time.timestamp())
    return (1, 0.0)


def build_equity_curve(
    trades: Sequence[SimulatedTrade],
    starting_capital: float,
    start_time: datetime | None = None,
) -> list[EquityPoint]:
    """Baut die Kapitalkurve aus den Trades.

    Args:
        trades: Die simulierten Trades (werden chronologisch sortiert).
        starting_capital: Startkapital (Kontowährung, > 0 empfohlen).
        start_time: Optionaler Zeitpunkt des Startpunkts.

    Returns:
        Eine Liste von :class:`EquityPoint`, beginnend mit dem Startpunkt.
    """
    equity = float(starting_capital)
    peak = equity
    points: list[EquityPoint] = [EquityPoint(start_time, equity, 0.0, 0.0)]
    for trade in sorted(trades, key=_sort_key):
        equity += trade.profit
        peak = max(peak, equity)
        drawdown = peak - equity
        drawdown_pct = (drawdown / peak * 100.0) if peak > 0 else 0.0
        points.append(EquityPoint(trade.exit_time, equity, drawdown, drawdown_pct))
    return points


def final_equity(curve: Sequence[EquityPoint], starting_capital: float) -> float:
    """Endkapital der Kurve (oder Startkapital bei leerer Kurve)."""
    if not curve:
        return float(starting_capital)
    return float(curve[-1].equity)


def maximum_drawdown(curve: Sequence[EquityPoint]) -> float:
    """Maximaler Drawdown der Kurve in Prozent (0..100)."""
    if not curve:
        return 0.0
    return float(max(point.drawdown_pct for point in curve))


def maximum_drawdown_abs(curve: Sequence[EquityPoint]) -> float:
    """Maximaler absoluter Drawdown der Kurve (Kontowährung)."""
    if not curve:
        return 0.0
    return float(max(point.drawdown for point in curve))
