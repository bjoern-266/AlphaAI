"""Ergebnistypen des Backtesting-Frameworks (Re-Export).

Die Definitionen liegen in der Entities-Schicht :mod:`models.backtest`. Dieses
Modul re-exportiert sie unter dem etablierten Pfad ``engines.backtest_result`` –
konsistent mit ``engines.risk_result`` und ``engines.recommendation_result``.
"""

from __future__ import annotations

from models.backtest import (
    PREPARED_RATIO_NAMES,
    BacktestContext,
    BacktestModelOutput,
    BacktestReport,
    BacktestResult,
    BenchmarkResult,
    EquityPoint,
    ExitReason,
    HistoricalSignal,
    SimulatedTrade,
    TradeOutcome,
)

__all__ = [
    "BacktestResult",
    "BacktestReport",
    "BacktestContext",
    "BacktestModelOutput",
    "BenchmarkResult",
    "EquityPoint",
    "ExitReason",
    "HistoricalSignal",
    "SimulatedTrade",
    "TradeOutcome",
    "PREPARED_RATIO_NAMES",
]
