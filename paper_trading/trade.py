"""Abgeschlossene Trades aus geschlossenen Positionen.

Reine Funktionen, die eine geschlossene
:class:`~models.paper_trading.PaperPosition` in einen unveränderlichen
:class:`~models.paper_trading.PaperTrade` überführen. Ein Trade fasst das
realisierte Ergebnis, die Haltedauer und die vollständige Rückverfolgbarkeit
(Recommendation-ID, Richtung, Stärke, Reasons, Warnings) zusammen.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from models.paper_trading import PaperPosition, PaperTrade, PositionStatus


def _holding_time(position: PaperPosition) -> timedelta | None:
    """Haltedauer aus Ein-/Ausstiegszeit (falls beide vorhanden)."""
    entry = position.entry_time
    exit_time = position.exit_time
    if isinstance(entry, datetime) and isinstance(exit_time, datetime):
        return exit_time - entry
    return None


def trade_from_position(position: PaperPosition, sequence: int = 0) -> PaperTrade:
    """Baut einen :class:`PaperTrade` aus einer geschlossenen Position."""
    return PaperTrade(
        trade_id=f"pt-trade:{position.position_id}:{sequence}",
        position_id=position.position_id,
        recommendation_id=position.recommendation_id,
        symbol=position.symbol,
        direction=position.direction,
        recommendation_strength=position.recommendation_strength,
        entry_price=position.entry_price,
        exit_price=position.exit_price,
        shares=position.shares,
        pnl=position.pnl,
        pnl_pct=position.pnl_pct,
        holding_time=_holding_time(position),
        close_reason=position.close_reason,
        reasons=list(position.reasons),
        warnings=list(position.warnings),
    )


def build_trades(positions: Sequence[PaperPosition]) -> list[PaperTrade]:
    """Baut Trades aus allen **geschlossenen** Positionen (Reihenfolge stabil)."""
    trades: list[PaperTrade] = []
    for index, position in enumerate(positions):
        if position.status is PositionStatus.CLOSED:
            trades.append(trade_from_position(position, index))
    return trades
