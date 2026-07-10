"""Trade-Simulator: aus bestehenden Empfehlungen simulierte Trades.

Der :class:`TradeSimulator` führt **keine** echte Order aus. Er nimmt die vom
Historical Runner erzeugten :class:`~models.backtest.HistoricalSignal` (jeweils
eine **bestehende** Empfehlung) und rechnet nach, wie sich der Trade anhand der
tatsächlichen künftigen Kerzen entwickelt hätte:

* Einstieg zum Schlusskurs der Signal-Kerze,
* Stop-Loss und Take-Profit aus den Abständen der Risk Engine
  (Positionsgröße/Risiko stammen ausschließlich aus ``settings.toml``),
* Ausstieg bei Erreichen von Stop, Take-Profit, maximaler Haltedauer oder am
  Ende der Daten.

Trifft eine Kerze **beide** Schwellen (Stop und Take-Profit), wird konservativ
der **Stop** angenommen. Es wird nie mehr als eine Position gleichzeitig
gehalten; Signale während einer offenen Position werden übersprungen.

Der Simulator erzeugt **keine** neue Handelsregel – er bewertet ausschließlich
bestehende Empfehlungen.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from models.backtest import (
    ExitReason,
    HistoricalSignal,
    SimulatedTrade,
    TradeOutcome,
)
from models.market import COL_CLOSE, COL_HIGH, COL_LOW
from models.recommendation import Direction


@dataclass(frozen=True, slots=True)
class SimulationParams:
    """Parameter der Trade-Simulation (aus ``backtest_rules.toml``).

    Attributes:
        max_holding_bars: Maximale Haltedauer in Kerzen bis zum Zeit-Ausstieg.
        apply_costs: Ob Kommission und Slippage vom Ergebnis abgezogen werden.
        breakeven_epsilon: Betragsgrenze (Kontowährung), unter der ein Trade als
            BREAKEVEN gilt.
    """

    max_holding_bars: int = 20
    apply_costs: bool = True
    breakeven_epsilon: float = 0.0


@dataclass
class _Exit:
    """Interner Ausstiegs-Zwischenstand."""

    index: int
    price: float
    reason: ExitReason


class TradeSimulator:
    """Simuliert Trades aus historischen Signalen (keine echte Order).

    Args:
        params: Parameter der Simulation (aus ``backtest_rules.toml``).
    """

    def __init__(self, params: SimulationParams) -> None:
        self._params = params

    def simulate(
        self, signals: Sequence[HistoricalSignal], frame: pd.DataFrame, symbol: str
    ) -> tuple[list[SimulatedTrade], list[str]]:
        """Simuliert alle actionablen Signale und liefert die Trades.

        Args:
            signals: Die historischen Signale (Einstiegskandidaten).
            frame: Der vollständige historische OHLCV-DataFrame.
            symbol: Symbolname (für die Trade-IDs).

        Returns:
            Ein Tupel ``(trades, warnings)``.
        """
        warnings: list[str] = []
        trades: list[SimulatedTrade] = []
        if frame is None or frame.empty:
            return trades, ["Keine Kursdaten für die Simulation."]
        for col in (COL_HIGH, COL_LOW, COL_CLOSE):
            if col not in frame.columns:
                return trades, [f"Spalte '{col}' fehlt – Simulation nicht möglich."]

        highs = frame[COL_HIGH].to_numpy(dtype=float)
        lows = frame[COL_LOW].to_numpy(dtype=float)
        closes = frame[COL_CLOSE].to_numpy(dtype=float)
        timestamps = list(frame.index)
        n = len(closes)

        open_until = -1
        for signal in sorted(signals, key=lambda s: s.bar_index):
            if not signal.is_actionable:
                continue
            if signal.bar_index <= open_until:
                continue  # Es wird nur eine Position gleichzeitig gehalten.
            trade = self._simulate_one(signal, symbol, highs, lows, closes, timestamps, n, warnings)
            if trade is None:
                continue
            trades.append(trade)
            open_until = signal.bar_index + trade.holding_bars
        return trades, warnings

    def _simulate_one(
        self,
        signal: HistoricalSignal,
        symbol: str,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        timestamps: list,
        n: int,
        warnings: list[str],
    ) -> SimulatedTrade | None:
        """Simuliert einen einzelnen Trade oder liefert ``None`` (nicht möglich)."""
        entry_index = signal.bar_index
        if entry_index < 0 or entry_index >= n - 1:
            warnings.append(
                f"Signal an Kerze {entry_index}: kein künftiger Kurs – kein Trade simulierbar."
            )
            return None

        entry_price = signal.entry_price
        is_long = signal.direction is Direction.LONG
        if is_long:
            stop_price = entry_price - signal.stop_distance
            take_profit_price = entry_price + signal.take_profit_distance
        else:
            stop_price = entry_price + signal.stop_distance
            take_profit_price = entry_price - signal.take_profit_distance

        last_index = min(entry_index + self._params.max_holding_bars, n - 1)
        exit_state = self._find_exit(
            is_long, entry_index, last_index, n, stop_price, take_profit_price, highs, lows, closes
        )

        gross = (
            (exit_state.price - entry_price) * signal.shares
            if is_long
            else (entry_price - exit_state.price) * signal.shares
        )
        costs = (signal.commission + signal.slippage) if self._params.apply_costs else 0.0
        profit = gross - costs
        position_value = signal.shares * entry_price
        profit_pct = (profit / position_value * 100.0) if position_value > 0 else 0.0
        return_on_risk = (profit / signal.risk_amount) if signal.risk_amount > 0 else 0.0
        holding_bars = exit_state.index - entry_index

        entry_time = _as_datetime(timestamps[entry_index])
        exit_time = _as_datetime(timestamps[exit_state.index])
        holding_time = (
            exit_time - entry_time
            if isinstance(entry_time, datetime) and isinstance(exit_time, datetime)
            else None
        )
        outcome = self._classify(profit)

        return SimulatedTrade(
            trade_id=f"bt:{symbol}:{entry_index}",
            symbol=symbol,
            direction=signal.direction,
            recommendation_strength=signal.recommendation_strength,
            recommendation_id=signal.recommendation_id,
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_state.price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            shares=signal.shares,
            risk_amount=signal.risk_amount,
            position_value=position_value,
            profit=profit,
            profit_pct=profit_pct,
            return_on_risk=return_on_risk,
            risk_reward=signal.risk_reward,
            holding_bars=holding_bars,
            holding_time=holding_time,
            outcome=outcome,
            exit_reason=exit_state.reason,
            commission=signal.commission if self._params.apply_costs else 0.0,
            slippage=signal.slippage if self._params.apply_costs else 0.0,
            reasons=list(signal.reasons),
            warnings=list(signal.warnings),
            metadata={"entry_index": entry_index, "exit_index": exit_state.index},
        )

    def _find_exit(
        self,
        is_long: bool,
        entry_index: int,
        last_index: int,
        n: int,
        stop_price: float,
        take_profit_price: float,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
    ) -> _Exit:
        """Ermittelt Ausstiegskerze, -preis und -grund (Stop hat Vorrang)."""
        for j in range(entry_index + 1, last_index + 1):
            high = float(highs[j])
            low = float(lows[j])
            if is_long:
                if low <= stop_price:
                    return _Exit(j, stop_price, ExitReason.STOP)
                if high >= take_profit_price:
                    return _Exit(j, take_profit_price, ExitReason.TAKE_PROFIT)
            else:
                if high >= stop_price:
                    return _Exit(j, stop_price, ExitReason.STOP)
                if low <= take_profit_price:
                    return _Exit(j, take_profit_price, ExitReason.TAKE_PROFIT)
        # Kein Stop/Take-Profit getroffen: Zeit- bzw. Datenende-Ausstieg zum Schlusskurs.
        reason = ExitReason.TIME if last_index < n - 1 else ExitReason.END_OF_DATA
        return _Exit(last_index, float(closes[last_index]), reason)

    def _classify(self, profit: float) -> TradeOutcome:
        """Ordnet dem Ergebnis einen Ausgang zu (mit Breakeven-Grenze)."""
        if abs(profit) <= self._params.breakeven_epsilon:
            return TradeOutcome.BREAKEVEN
        return TradeOutcome.WIN if profit > 0 else TradeOutcome.LOSS


def _as_datetime(value: object) -> datetime | None:
    """Wandelt einen Index-Eintrag – falls möglich – in ein ``datetime`` um."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return None
