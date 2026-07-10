"""Positions-Management für das simulierte Portfolio.

Reine Funktionen, die eine :class:`~models.paper_trading.PaperPosition`
**unveränderlich** fortschreiben (jede Änderung erzeugt eine neue Instanz via
``dataclasses.replace``). Enthalten sind: Eröffnen, Mark-to-Market (aktueller
Preis + PnL), Erkennen eines Ausstiegs (Stop/Take-Profit), Schließen, Stornieren
und ein **vorbereiteter** Trailing-Stop.

Es wird **keine** echte Order ausgeführt und **keine** Handelsregel erzeugt – die
Richtung, Stop-/Take-Profit-Abstände und die Stückzahl stammen aus der
bestehenden Empfehlung bzw. Risk Engine.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from models.paper_trading import CloseReason, PaperPosition, PositionStatus
from models.recommendation import Direction, RecommendationStrength


def compute_pnl(direction: Direction, entry_price: float, price: float, shares: float) -> float:
    """Berechnet das (un-)realisierte Ergebnis in Kontowährung."""
    if direction is Direction.SHORT:
        return (entry_price - price) * shares
    return (price - entry_price) * shares


def _pnl_pct(pnl: float, position_size: float) -> float:
    """Ergebnis relativ zum Positionswert (Prozent)."""
    return (pnl / position_size * 100.0) if position_size > 0 else 0.0


def open_position(
    position_id: str,
    recommendation_id: str,
    symbol: str,
    direction: Direction,
    recommendation_strength: RecommendationStrength,
    entry_price: float,
    stop_price: float,
    take_profit_price: float,
    shares: float,
    risk_amount: float,
    entry_time: datetime | None,
    reasons: list[str] | None = None,
    warnings: list[str] | None = None,
    metadata: dict | None = None,
) -> PaperPosition:
    """Erzeugt eine neue **offene** Position (ohne Portfolio-Validierung)."""
    return PaperPosition(
        position_id=position_id,
        recommendation_id=recommendation_id,
        symbol=symbol,
        direction=direction,
        recommendation_strength=recommendation_strength,
        status=PositionStatus.OPEN,
        entry_price=entry_price,
        current_price=entry_price,
        stop_price=stop_price,
        take_profit_price=take_profit_price,
        shares=shares,
        position_size=shares * entry_price,
        risk_amount=risk_amount,
        entry_time=entry_time,
        reasons=list(reasons or []),
        warnings=list(warnings or []),
        metadata=dict(metadata or {}),
    )


def mark_to_market(
    position: PaperPosition, price: float, timestamp: datetime | None
) -> PaperPosition:
    """Bewertet eine offene Position zum aktuellen Preis (unrealisierter PnL)."""
    if not position.is_open:
        return position
    pnl = compute_pnl(position.direction, position.entry_price, price, position.shares)
    metadata = {**position.metadata, "last_update": timestamp}
    return replace(
        position,
        current_price=price,
        pnl=pnl,
        pnl_pct=_pnl_pct(pnl, position.position_size),
        metadata=metadata,
    )


def detect_exit(
    position: PaperPosition, high: float, low: float, close: float
) -> tuple[CloseReason | None, float]:
    """Prüft, ob eine offene Position austeigt (Stop hat Vorrang vor Take-Profit).

    Args:
        position: Die offene Position.
        high: Tageshoch.
        low: Tagestief.
        close: Tagesschluss.

    Returns:
        Ein Tupel ``(reason, price)``. ``reason`` ist ``None``, wenn kein
        Ausstieg ausgelöst wird.
    """
    if not position.is_open:
        return None, close
    if position.direction is Direction.SHORT:
        if position.stop_price > 0 and high >= position.stop_price:
            return CloseReason.STOP, position.stop_price
        if position.take_profit_price > 0 and low <= position.take_profit_price:
            return CloseReason.TAKE_PROFIT, position.take_profit_price
        return None, close
    if position.stop_price > 0 and low <= position.stop_price:
        return CloseReason.STOP, position.stop_price
    if position.take_profit_price > 0 and high >= position.take_profit_price:
        return CloseReason.TAKE_PROFIT, position.take_profit_price
    return None, close


def close_position(
    position: PaperPosition,
    price: float,
    timestamp: datetime | None,
    reason: CloseReason,
) -> PaperPosition:
    """Schließt eine offene Position (realisierter PnL)."""
    pnl = compute_pnl(position.direction, position.entry_price, price, position.shares)
    return replace(
        position,
        status=PositionStatus.CLOSED,
        current_price=price,
        exit_price=price,
        exit_time=timestamp,
        close_reason=reason,
        pnl=pnl,
        pnl_pct=_pnl_pct(pnl, position.position_size),
    )


def cancel_position(position: PaperPosition, timestamp: datetime | None) -> PaperPosition:
    """Storniert eine offene Position (kein PnL)."""
    return replace(
        position,
        status=PositionStatus.CANCELLED,
        exit_time=timestamp,
        pnl=0.0,
        pnl_pct=0.0,
    )


def apply_trailing_stop(
    position: PaperPosition, price: float, trailing_distance: float
) -> PaperPosition:
    """Zieht den Stop einer offenen Position nach (**vorbereitet**).

    Standardmäßig **inaktiv** (``trailing_distance <= 0`` gibt die Position
    unverändert zurück). Bei aktivem Trailing wird der Stop – nur in
    Gewinnrichtung – nachgezogen und in ``trailing_stop_price`` sowie
    ``stop_price`` gespiegelt.
    """
    if trailing_distance <= 0 or not position.is_open:
        return position
    if position.direction is Direction.SHORT:
        candidate = price + trailing_distance
        if position.stop_price <= 0 or candidate < position.stop_price:
            return replace(position, stop_price=candidate, trailing_stop_price=candidate)
        return position
    candidate = price - trailing_distance
    if candidate > position.stop_price:
        return replace(position, stop_price=candidate, trailing_stop_price=candidate)
    return position
