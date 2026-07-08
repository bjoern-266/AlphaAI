"""Gemeinsame Schnittstelle und Hilfsmittel für Indikatoren.

Alle Indikatoren implementieren :class:`BaseIndicator` und geben ihr Ergebnis
als :class:`IndicatorOutput` zurück. Die Hilfsfunktionen stellen sicher, dass
Parameter ausschließlich aus der Konfiguration stammen (kein stiller Default)
und dass Division durch Null kontrolliert behandelt wird.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd


class IndicatorParameterError(ValueError):
    """Wird ausgelöst, wenn ein Pflichtparameter fehlt oder ungültig ist."""


@dataclass(slots=True)
class IndicatorOutput:
    """Ergebnis eines einzelnen Indikators.

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


class BaseIndicator(ABC):
    """Basisklasse für alle technischen Indikatoren.

    Attributes:
        name: Eindeutiger Indikatorname (z. B. ``"ema"``).
        requires_volume: Ob der Indikator Volumendaten benötigt.
    """

    name: str = "base"
    requires_volume: bool = False

    @abstractmethod
    def compute(self, data: pd.DataFrame, params: Mapping[str, Any]) -> IndicatorOutput:
        """Berechnet den Indikator auf den übergebenen OHLCV-Daten.

        Args:
            data: OHLCV-DataFrame im kanonischen Schema.
            params: Parameter des Indikators (aus der Konfiguration).

        Returns:
            Das :class:`IndicatorOutput`.
        """
        raise NotImplementedError

    @abstractmethod
    def min_candles(self, params: Mapping[str, Any]) -> int:
        """Gibt die minimal benötigte Anzahl an Kerzen zurück.

        Args:
            params: Parameter des Indikators (aus der Konfiguration).
        """
        raise NotImplementedError


def require_int(params: Mapping[str, Any], key: str, indicator: str) -> int:
    """Liest einen ganzzahligen Pflichtparameter.

    Raises:
        IndicatorParameterError: Wenn der Parameter fehlt oder keine positive
            Ganzzahl ist.
    """
    if key not in params:
        raise IndicatorParameterError(f"Indikator '{indicator}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise IndicatorParameterError(
            f"Indikator '{indicator}': Parameter '{key}' muss eine positive Ganzzahl sein."
        )
    return value


def require_float(params: Mapping[str, Any], key: str, indicator: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (> 0).

    Raises:
        IndicatorParameterError: Wenn der Parameter fehlt oder ungültig ist.
    """
    if key not in params:
        raise IndicatorParameterError(f"Indikator '{indicator}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise IndicatorParameterError(
            f"Indikator '{indicator}': Parameter '{key}' muss eine positive Zahl sein."
        )
    return float(value)


def require_int_list(params: Mapping[str, Any], key: str, indicator: str) -> list[int]:
    """Liest eine Liste positiver Ganzzahlen als Pflichtparameter.

    Raises:
        IndicatorParameterError: Wenn der Parameter fehlt oder ungültig ist.
    """
    if key not in params:
        raise IndicatorParameterError(f"Indikator '{indicator}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, (list, tuple)) or not value:
        raise IndicatorParameterError(
            f"Indikator '{indicator}': Parameter '{key}' muss eine nicht-leere Liste sein."
        )
    result: list[int] = []
    for item in value:
        if not isinstance(item, int) or isinstance(item, bool) or item <= 0:
            raise IndicatorParameterError(
                f"Indikator '{indicator}': '{key}' darf nur positive Ganzzahlen enthalten."
            )
        result.append(item)
    return result


def true_range(data: pd.DataFrame) -> pd.Series:
    """Berechnet die True Range aus High, Low und vorherigem Close.

    Die True Range ist das Maximum aus ``High-Low``, ``|High-Close_vorher|``
    und ``|Low-Close_vorher|``. Diese Funktion ist ein gemeinsames Hilfsmittel
    (kein eigener Indikator) und wird u. a. von ATR und ADX genutzt, damit kein
    Indikator von einem anderen Indikator abhängt.
    """
    high = data["high"]
    low = data["low"]
    prev_close = data["close"].shift(1)
    ranges = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    )
    return ranges.max(axis=1)


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Teilt zwei Serien und ersetzt Division durch Null durch ``NaN``.

    Args:
        numerator: Zähler-Serie.
        denominator: Nenner-Serie.

    Returns:
        Ergebnis-Serie; an Stellen mit Nenner 0 steht ``NaN``.
    """
    with np.errstate(divide="ignore", invalid="ignore"):
        result = numerator / denominator.replace(0, np.nan)
    return result.replace([np.inf, -np.inf], np.nan)


def has_usable_volume(data: pd.DataFrame) -> bool:
    """Prüft, ob nutzbare Volumendaten vorhanden sind.

    Volumen gilt als fehlend, wenn die Spalte fehlt, ausschließlich ``NaN``
    enthält oder durchgehend 0 ist.
    """
    if "volume" not in data.columns:
        return False
    volume = data["volume"]
    if volume.isna().all():
        return False
    return not bool((volume.fillna(0) == 0).all())


def clean_value(value: float) -> float | None:
    """Wandelt ``NaN``/Unendlich in ``None`` um, sonst ``float``."""
    if value is None or math.isnan(value) or math.isinf(value):
        return None
    return float(value)
