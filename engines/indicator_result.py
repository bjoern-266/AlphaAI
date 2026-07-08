"""Aggregiertes Ergebnis der Indicator Engine.

:class:`IndicatorResult` bündelt die Ausgaben aller berechneten Indikatoren für
**ein** Symbol und bietet bequeme, typisierte Zugriffe auf die wichtigsten
Kennzahlen (z. B. ``ema20``, ``rsi14``). Die Rohserien bleiben über
:attr:`outputs` vollständig zugänglich.

Das Ergebnis enthält **keine** Bewertung, keinen Score und kein Signal – nur
berechnete Kennzahlen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from indicators.base import IndicatorOutput


@dataclass(slots=True)
class IndicatorResult:
    """Ergebnis der Indikatorberechnung für ein Symbol.

    Attributes:
        outputs: Zuordnung Indikatorname -> :class:`IndicatorOutput`.
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist (genug Historie,
            keine strukturellen Fehler).
        warnings: Gesammelte Warnungen (z. B. übersprungene Indikatoren).
        metadata: Zusatzinformationen (Symbol, Timeframe, Kerzenanzahl, …).
    """

    outputs: dict[str, IndicatorOutput] = field(default_factory=dict)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def output(self, name: str) -> IndicatorOutput | None:
        """Gibt die Ausgabe eines Indikators zurück oder ``None``."""
        return self.outputs.get(name)

    def _latest(self, indicator: str, component: str) -> float | None:
        """Letzter gültiger Wert einer Indikatorkomponente oder ``None``."""
        out = self.outputs.get(indicator)
        if out is None:
            return None
        return out.latest(component)

    # --- Bequeme, typisierte Zugriffe (Standard-Parameter aus der Config) ---

    @property
    def ema20(self) -> float | None:
        """Letzter EMA(20)."""
        return self._latest("ema", "ema_20")

    @property
    def ema50(self) -> float | None:
        """Letzter EMA(50)."""
        return self._latest("ema", "ema_50")

    @property
    def ema200(self) -> float | None:
        """Letzter EMA(200)."""
        return self._latest("ema", "ema_200")

    @property
    def rsi14(self) -> float | None:
        """Letzter RSI(14)."""
        return self._latest("rsi", "rsi_14")

    @property
    def atr14(self) -> float | None:
        """Letzter ATR(14)."""
        return self._latest("atr", "atr_14")

    @property
    def vwap(self) -> float | None:
        """Letzter VWAP."""
        return self._latest("vwap", "vwap")

    @property
    def macd(self) -> float | None:
        """Letzte MACD-Linie."""
        return self._latest("macd", "macd")

    @property
    def macd_signal(self) -> float | None:
        """Letzte MACD-Signallinie."""
        return self._latest("macd", "signal")

    @property
    def macd_histogram(self) -> float | None:
        """Letztes MACD-Histogramm."""
        return self._latest("macd", "histogram")

    @property
    def relative_volume(self) -> float | None:
        """Letztes relatives Volumen."""
        return self._latest("relative_volume", "relative_volume")

    @property
    def adx(self) -> float | None:
        """Letzter ADX."""
        return self._latest("adx", "adx")

    @property
    def bollinger_bands(self) -> dict[str, float | None]:
        """Letzte Bollinger-Bänder als ``{upper, middle, lower}``."""
        return {
            "upper": self._latest("bollinger", "upper"),
            "middle": self._latest("bollinger", "middle"),
            "lower": self._latest("bollinger", "lower"),
        }

    @property
    def stochastic(self) -> dict[str, float | None]:
        """Letzte Stochastik als ``{percent_k, percent_d}``."""
        return {
            "percent_k": self._latest("stochastic", "percent_k"),
            "percent_d": self._latest("stochastic", "percent_d"),
        }

    @property
    def obv(self) -> float | None:
        """Letzter OBV-Wert."""
        return self._latest("obv", "obv")

    @property
    def volume_profile(self) -> pd.Series | None:
        """Volumenverteilung (Serie: Preis-Bin -> Volumen) oder ``None``."""
        out = self.outputs.get("volume_profile")
        if out is None:
            return None
        return out.series.get("volume_profile")

    @property
    def volume_profile_poc(self) -> float | None:
        """Point of Control des Volume Profile oder ``None``."""
        out = self.outputs.get("volume_profile")
        if out is None:
            return None
        poc = out.extra.get("poc")
        return float(poc) if poc is not None else None

    def summary(self) -> dict[str, Any]:
        """Kompakte Übersicht der wichtigsten letzten Kennzahlen."""
        return {
            "ema20": self.ema20,
            "ema50": self.ema50,
            "ema200": self.ema200,
            "rsi14": self.rsi14,
            "atr14": self.atr14,
            "vwap": self.vwap,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "macd_histogram": self.macd_histogram,
            "relative_volume": self.relative_volume,
            "adx": self.adx,
            "bollinger_bands": self.bollinger_bands,
            "stochastic": self.stochastic,
            "obv": self.obv,
            "volume_profile_poc": self.volume_profile_poc,
        }
