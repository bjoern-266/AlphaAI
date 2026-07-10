"""Risikoadjustierte Kennzahlen (**vorbereitet**).

Sharpe-, Sortino- und Calmar-Ratio sind hier mit ihren mathematischen
Standardformeln implementiert, aber bewusst **vorbereitet**: sie werden nicht
annualisiert und nicht gegen eine kalibrierte Referenz-Periodizität gerechnet,
bis ein realer Datensatz und eine belastbare Periodizität feststehen (siehe
``docs/VALIDATION_REPORT.md``). Sie geben ``None`` zurück, wenn zu wenige Daten
für eine sinnvolle Aussage vorliegen – nie einen irreführenden Zahlenwert.

Reine, seiteneffektfreie Funktionen. Kein Zustand, keine Handelsregel.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from models.backtest import SimulatedTrade


def trade_returns(trades: Sequence[SimulatedTrade]) -> list[float]:
    """Renditen je Trade als Bruchteil des Positionswerts (0.02 = 2 %)."""
    return [t.profit_pct / 100.0 for t in trades]


def _mean(values: Sequence[float]) -> float:
    """Arithmetisches Mittel."""
    return sum(values) / len(values)


def _std(values: Sequence[float], mean: float) -> float:
    """Standardabweichung (Stichprobe, n-1)."""
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(variance)


def sharpe_ratio(
    returns: Sequence[float], risk_free_rate: float = 0.0, periods_per_year: int = 0
) -> float | None:
    """Sharpe-Ratio (vorbereitet).

    Überschussrendite geteilt durch die Standardabweichung. Optional mit
    ``periods_per_year`` annualisiert (``0`` = nicht annualisiert). ``None``,
    wenn weniger als zwei Renditen vorliegen oder die Streuung null ist.
    """
    if len(returns) < 2:
        return None
    excess = [r - risk_free_rate for r in returns]
    mean = _mean(excess)
    std = _std(excess, mean)
    if std == 0.0:
        return None
    ratio = mean / std
    if periods_per_year > 0:
        ratio *= math.sqrt(periods_per_year)
    return float(ratio)


def sortino_ratio(
    returns: Sequence[float], risk_free_rate: float = 0.0, periods_per_year: int = 0
) -> float | None:
    """Sortino-Ratio (vorbereitet).

    Wie Sharpe, aber nur die **Abwärts**-Abweichung geht in den Nenner ein.
    ``None``, wenn weniger als zwei Renditen vorliegen oder es keine (bzw. keine
    streuende) Abwärtsbewegung gibt.
    """
    if len(returns) < 2:
        return None
    excess = [r - risk_free_rate for r in returns]
    mean = _mean(excess)
    downside = [min(0.0, e) for e in excess]
    downside_var = sum(d**2 for d in downside) / len(downside)
    downside_dev = math.sqrt(downside_var)
    if downside_dev == 0.0:
        return None
    ratio = mean / downside_dev
    if periods_per_year > 0:
        ratio *= math.sqrt(periods_per_year)
    return float(ratio)


def calmar_ratio(total_return_pct: float, maximum_drawdown_pct: float) -> float | None:
    """Calmar-Ratio (vorbereitet): Gesamtrendite / maximaler Drawdown.

    ``None``, wenn kein (positiver) Drawdown vorliegt, da das Verhältnis dann
    nicht sinnvoll definiert ist.
    """
    if maximum_drawdown_pct <= 0.0:
        return None
    return float(total_return_pct / maximum_drawdown_pct)
