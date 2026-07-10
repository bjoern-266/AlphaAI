"""Reine Kennzahl-Berechnungen über simulierte Trades.

Alle Funktionen sind **rein** (ohne Seiteneffekt) und arbeiten ausschließlich
auf einer Sequenz von :class:`~models.backtest.SimulatedTrade`. Sie bilden die
dokumentierten Messungen der Backtest-Kennzahlen ab; es gibt keine
hartcodierten Handelsregeln, nur mathematische Definitionen.

Konventionen:

* Ergebnisse ohne Trades sind neutral (``0.0``), nicht ``NaN``.
* ``average_loss`` wird als **negativer** Betrag geliefert (tatsächliches PnL).
* ``profit_factor`` ist ``inf``, wenn es keine Verluste gibt, aber Gewinne.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from models.backtest import SimulatedTrade


def total_profit(trades: Sequence[SimulatedTrade]) -> float:
    """Summe aller Netto-Ergebnisse (Kontowährung)."""
    return float(sum(t.profit for t in trades))


def gross_profit(trades: Sequence[SimulatedTrade]) -> float:
    """Summe der Gewinne (nur positive Ergebnisse)."""
    return float(sum(t.profit for t in trades if t.profit > 0.0))


def gross_loss(trades: Sequence[SimulatedTrade]) -> float:
    """Summe der Verluste als **positiver** Betrag (|negative Ergebnisse|)."""
    return float(sum(-t.profit for t in trades if t.profit < 0.0))


def win_rate(trades: Sequence[SimulatedTrade]) -> float:
    """Trefferquote 0..1 (Anteil der Gewinn-Trades)."""
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.is_win)
    return wins / len(trades)


def loss_rate(trades: Sequence[SimulatedTrade]) -> float:
    """Verlustquote 0..1 (Anteil der Verlust-Trades)."""
    if not trades:
        return 0.0
    losses = sum(1 for t in trades if t.is_loss)
    return losses / len(trades)


def profit_factor(trades: Sequence[SimulatedTrade]) -> float:
    """Bruttogewinn / Bruttoverlust.

    Ohne Trades ``0.0``; ohne Verluste (aber mit Gewinnen) ``inf``; ohne
    Gewinne und ohne Verluste ``0.0``.
    """
    if not trades:
        return 0.0
    profit = gross_profit(trades)
    loss = gross_loss(trades)
    if loss == 0.0:
        return math.inf if profit > 0.0 else 0.0
    return profit / loss


def average_win(trades: Sequence[SimulatedTrade]) -> float:
    """Durchschnittlicher Gewinn der Gewinn-Trades (≥ 0)."""
    wins = [t.profit for t in trades if t.is_win]
    if not wins:
        return 0.0
    return float(sum(wins) / len(wins))


def average_loss(trades: Sequence[SimulatedTrade]) -> float:
    """Durchschnittlicher Verlust der Verlust-Trades (≤ 0, als PnL)."""
    losses = [t.profit for t in trades if t.is_loss]
    if not losses:
        return 0.0
    return float(sum(losses) / len(losses))


def average_risk_reward(trades: Sequence[SimulatedTrade]) -> float:
    """Durchschnittliches geplantes Chance-Risiko-Verhältnis der Trades."""
    if not trades:
        return 0.0
    return float(sum(t.risk_reward for t in trades) / len(trades))


def average_holding_time(trades: Sequence[SimulatedTrade]) -> float:
    """Durchschnittliche Haltedauer in Kerzen (Bars)."""
    if not trades:
        return 0.0
    return float(sum(t.holding_bars for t in trades) / len(trades))


def expectancy(trades: Sequence[SimulatedTrade]) -> float:
    """Erwartungswert je Trade (Kontowährung) = mittleres Netto-Ergebnis.

    Entspricht ``win_rate * average_win + loss_rate * average_loss`` und damit
    dem durchschnittlichen PnL je Trade.
    """
    if not trades:
        return 0.0
    return float(total_profit(trades) / len(trades))


def expectancy_r(trades: Sequence[SimulatedTrade]) -> float:
    """Erwartungswert je Trade als R-Vielfaches (mittlere Rendite auf Risiko)."""
    values = [t.return_on_risk for t in trades if t.risk_amount > 0.0]
    if not values:
        return 0.0
    return float(sum(values) / len(values))
