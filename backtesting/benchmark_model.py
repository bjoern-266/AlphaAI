"""Benchmark Model – Vergleich gegen einen Referenzmaßstab.

Vergleicht die Gesamtrendite der AlphaAI-Empfehlungen mit dem vorab berechneten
Benchmark (z. B. Buy & Hold) aus dem Kontext und liefert das Alpha
(Differenz der Renditen). Der Vergleich ist reine **Referenz** und **keine**
Handelsentscheidung. Kein anderes Modell wird importiert.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from backtesting import equity_curve as ec
from backtesting.base import BacktestContext, BacktestModelOutput, BaseBacktestModel


class BenchmarkModel(BaseBacktestModel):
    """Vergleicht die Strategie-Rendite mit dem Benchmark (z. B. Buy & Hold)."""

    name = "benchmark_model"
    value_range = "Alpha (Renditedifferenz in %)"

    def compute(self, context: BacktestContext, params: Mapping[str, Any]) -> BacktestModelOutput:
        """Erzeugt den Benchmark-Vergleich (Alpha), falls eine Referenz vorliegt."""
        benchmark = context.benchmark
        if benchmark is None:
            return BacktestModelOutput(
                name=self.name,
                reasons=["Kein Benchmark verfügbar – Vergleich übersprungen."],
                details={"benchmark": None},
            )
        capital = context.starting_capital
        final = ec.final_equity(context.equity_curve, capital)
        strategy_return_pct = ((final - capital) / capital * 100.0) if capital > 0 else 0.0
        alpha = strategy_return_pct - benchmark.return_pct
        reasons = [
            f"AlphaAI {strategy_return_pct:+.2f} % vs. {benchmark.name} "
            f"{benchmark.return_pct:+.2f} % ⇒ Alpha {alpha:+.2f} %."
        ]
        return BacktestModelOutput(
            name=self.name,
            metrics={"benchmark_return_pct": benchmark.return_pct, "alpha": alpha},
            reasons=reasons,
            details={"benchmark": benchmark},
        )
