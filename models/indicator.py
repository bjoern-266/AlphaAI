"""Domänenmodell: Indikator-Ergebnisse.

Enthält die unveränderlichen Ergebnisobjekte der Indicator Engine:
:class:`IndicatorOutput` (Ausgabe eines einzelnen Indikators) und
:class:`IndicatorResult` (aggregiertes Ergebnis für ein Symbol). Teil der
Entities-Schicht (``models/``) – importiert nichts aus höheren Schichten.

Re-exportiert unter ``indicators.base`` (``IndicatorOutput``) bzw.
``engines.indicator_result`` (``IndicatorResult``) zur Rückwärtskompatibilität.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass(frozen=True, slots=True)
class IndicatorOutput:
    """Ergebnis eines einzelnen Indikators (unveränderlich).

    Attributes:
        name: Name des Indikators.
        series: Zuordnung Komponentenname -> berechnete Zeitreihe (z. B.
            ``"ema_20"`` -> Serie). Enthält die vollständige Historie.
        warnings: Während der Berechnung gesammelte Warnungen.
        extra: Zusätzliche skalare Kennzahlen (z. B. Point of Control beim
            Volume Profile), die keine Zeitreihe sind.
    """

    name: str
    series: dict[str, pd.Series] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def latest(self, component: str) -> float | None:
        """Gibt den letzten gültigen Wert einer Komponente zurück.

        Args:
            component: Name der Komponente (z. B. ``"ema_20"``).

        Returns:
            Der letzte nicht-NaN-Wert als ``float`` oder ``None``.
        """
        series = self.series.get(component)
        if series is None:
            return None
        cleaned = series.dropna()
        if cleaned.empty:
            return None
        return float(cleaned.iloc[-1])

    def latest_all(self) -> dict[str, float | None]:
        """Gibt die letzten gültigen Werte aller Komponenten zurück."""
        return {name: self.latest(name) for name in self.series}


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    """Ergebnis der Indikatorberechnung für ein Symbol (unveränderlich).

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
