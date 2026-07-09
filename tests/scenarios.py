"""Deterministische, echte OHLCV-Marktszenarien für die Integrations-Tests.

Kein Mock: jede Funktion liefert einen vollständigen OHLCV-DataFrame im
kanonischen Schema, der durch die **echte** Pipeline läuft. Alle Zufalls-Serien
sind geseedet und damit reproduzierbar.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

N = 240  # genügend Historie für alle Indikatoren (inkl. EMA200)


def _ohlcv(
    closes: np.ndarray,
    volume: float | np.ndarray = 1_000_000.0,
    opens: np.ndarray | None = None,
    start: str = "2023-01-01",
) -> pd.DataFrame:
    """Baut einen kanonischen OHLCV-DataFrame aus Schlusskursen."""
    c = np.asarray(closes, dtype=float)
    n = len(c)
    index = pd.date_range(start=start, periods=n, freq="D")
    o = np.asarray(opens, dtype=float) if opens is not None else np.concatenate([[c[0]], c[:-1]])
    span = np.abs(c) * 0.005 + 0.5
    high = np.maximum(o, c) + span
    low = np.minimum(o, c) - span
    vol = np.asarray(volume, dtype=float) if np.ndim(volume) else np.full(n, float(volume))
    return pd.DataFrame(
        {"open": o, "high": high, "low": low, "close": c, "adj_close": c, "volume": vol},
        index=index,
    )


def trend_up(n: int = N, slope: float = 0.3, base: float = 100.0) -> pd.DataFrame:
    """Stetiger Aufwärtstrend."""
    return _ohlcv(base + slope * np.arange(n))


def trend_down(n: int = N, slope: float = 0.3, base: float = 180.0) -> pd.DataFrame:
    """Stetiger Abwärtstrend."""
    return _ohlcv(np.maximum(base - slope * np.arange(n), 5.0))


def sideways(n: int = N, base: float = 100.0, amp: float = 1.5) -> pd.DataFrame:
    """Seitwärtsmarkt (Oszillation um ein Niveau)."""
    return _ohlcv(base + amp * np.sin(np.linspace(0, 20 * np.pi, n)))


def high_volatility(n: int = N, base: float = 100.0, seed: int = 1) -> pd.DataFrame:
    """Hohe Volatilität (große, zufällige Schwankungen)."""
    rng = np.random.default_rng(seed)
    closes = base + np.cumsum(rng.normal(0.3, 4.0, n))
    return _ohlcv(np.maximum(closes, 5.0))


def low_volatility(n: int = N, base: float = 100.0, slope: float = 0.12) -> pd.DataFrame:
    """Niedrige Volatilität (ruhiger, leichter Aufwärtsdrift)."""
    return _ohlcv(base + slope * np.arange(n) + 0.05 * np.sin(np.arange(n)))


def breakout_up(n: int = N, base: float = 100.0) -> pd.DataFrame:
    """Bullischer Ausbruch (Seitwärts, dann scharfer Anstieg)."""
    half = n // 2
    flat = base + 0.3 * np.sin(np.linspace(0, 10 * np.pi, half))
    up = flat[-1] + 0.8 * np.arange(n - half)
    return _ohlcv(np.concatenate([flat, up]))


def breakout_down(n: int = N, base: float = 160.0) -> pd.DataFrame:
    """Bärischer Ausbruch (Seitwärts, dann scharfer Rückgang)."""
    half = n // 2
    flat = base + 0.3 * np.sin(np.linspace(0, 10 * np.pi, half))
    down = np.maximum(flat[-1] - 0.8 * np.arange(n - half), 5.0)
    return _ohlcv(np.concatenate([flat, down]))


def low_liquidity(n: int = N) -> pd.DataFrame:
    """Niedrige Liquidität (Aufwärtstrend, aber winziges Volumen)."""
    return _ohlcv(100.0 + 0.3 * np.arange(n), volume=500.0)


def high_liquidity(n: int = N) -> pd.DataFrame:
    """Hohe Liquidität (Aufwärtstrend, sehr großes Volumen)."""
    return _ohlcv(100.0 + 0.3 * np.arange(n), volume=50_000_000.0)


def gap_heavy(n: int = N, base: float = 100.0, seed: int = 2) -> pd.DataFrame:
    """Viele große Overnight-Gaps (hohes Gap-Risiko)."""
    rng = np.random.default_rng(seed)
    closes = base + 0.3 * np.arange(n)
    opens = closes + rng.choice([-6.0, -4.0, 4.0, 6.0], n)
    return _ohlcv(closes, opens=opens)


def choppy(n: int = N, base: float = 100.0, seed: int = 3) -> pd.DataFrame:
    """Richtungsloser Random-Walk (potenzieller Strategie-Konflikt)."""
    rng = np.random.default_rng(seed)
    closes = np.maximum(base + np.cumsum(rng.normal(0.0, 1.5, n)), 5.0)
    return _ohlcv(closes)


def weak_data_quality(n: int = N) -> pd.DataFrame:
    """Schwache Datenqualität (NaN-Lücken in den Schlusskursen)."""
    frame = trend_up(n)
    frame.iloc[::10, frame.columns.get_loc("close")] = np.nan
    return frame


def short_history(n: int = 20) -> pd.DataFrame:
    """Zu wenig Historie (Indikatoren werden ungültig)."""
    return trend_up(n)


# Register aller Szenarien für die parametrisierten Integrations-Tests.
SCENARIOS: dict[str, Callable[[], pd.DataFrame]] = {
    "trend_up": trend_up,
    "trend_down": trend_down,
    "sideways": sideways,
    "high_volatility": high_volatility,
    "low_volatility": low_volatility,
    "breakout_up": breakout_up,
    "breakout_down": breakout_down,
    "low_liquidity": low_liquidity,
    "high_liquidity": high_liquidity,
    "gap_heavy": gap_heavy,
    "choppy": choppy,
    "weak_data_quality": weak_data_quality,
    "short_history": short_history,
}
