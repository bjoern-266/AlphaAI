"""Vergleichsmaßstäbe (Benchmarks) für den Backtest.

Aktuell ist **Buy & Hold** implementiert: Kauf zum ersten Schlusskurs des
Zeitraums, Halten bis zum letzten Schlusskurs. Der Benchmark dient
ausschließlich als **Referenz** – er ist keine Empfehlung und keine
Handelsregel. Fractional Shares werden vollständig unterstützt (das gesamte
Startkapital wird investiert).

Reine, seiteneffektfreie Funktionen auf einem kanonischen OHLCV-DataFrame.
"""

from __future__ import annotations

import pandas as pd

from models.backtest import BenchmarkResult
from models.market import COL_CLOSE


def buy_and_hold(
    frame: pd.DataFrame, starting_capital: float, name: str = "buy_and_hold"
) -> BenchmarkResult | None:
    """Berechnet den Buy-&-Hold-Vergleich über den Zeitraum des DataFrames.

    Args:
        frame: Kanonischer OHLCV-DataFrame (Spalte ``close`` erforderlich).
        starting_capital: Startkapital (Kontowährung).
        name: Name der Referenz.

    Returns:
        Ein :class:`BenchmarkResult` oder ``None``, wenn keine gültigen
        Preise vorliegen (leere Daten, fehlende Spalte, Preis ≤ 0).
    """
    if frame is None or frame.empty or COL_CLOSE not in frame.columns:
        return None
    closes = frame[COL_CLOSE].dropna()
    if closes.empty:
        return None
    start_price = float(closes.iloc[0])
    end_price = float(closes.iloc[-1])
    if start_price <= 0.0 or starting_capital <= 0.0:
        return None

    shares = starting_capital / start_price
    end_equity = shares * end_price
    return_pct = (end_equity / starting_capital - 1.0) * 100.0
    return BenchmarkResult(
        name=name,
        start_price=start_price,
        end_price=end_price,
        start_equity=float(starting_capital),
        end_equity=float(end_equity),
        return_pct=float(return_pct),
        reasons=[
            f"Buy & Hold: Kauf zu {start_price:.2f}, Verkauf zu {end_price:.2f} "
            f"({shares:.4f} Stück) ⇒ {return_pct:+.2f} %."
        ],
    )
