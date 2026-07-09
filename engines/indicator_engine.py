"""Indicator Engine – berechnet technische Indikatoren.

Die :class:`IndicatorEngine` nimmt Marktdaten (einen OHLCV-DataFrame bzw. ein
:class:`~data.market_result.MarketResult`) entgegen und liefert ein
:class:`~engines.indicator_result.IndicatorResult`. Sie orchestriert die
registrierten Indikatoren, validiert die Eingabe und cached Ergebnisse
optional. Sie trifft **keine** Handelsentscheidungen, erzeugt **keine** Scores
und **keine** Signale.

Parameter stammen ausschließlich aus ``knowledge/indicator_rules.toml`` – im
Code gibt es keine hartcodierten Indikatorparameter.

Multi-Timeframe: Die Methoden nehmen bereits ein ``timeframe``-Label entgegen
und legen es in den Metadaten ab. Die tatsächliche Berechnung über mehrere
Zeitebenen ist damit vorbereitet, aber **noch nicht** implementiert (ein
späterer Aggregator würde die Engine je Zeitebene aufrufen und die Ergebnisse
zusammenführen).
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pandas as pd

from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import INDICATOR_RULES_FILE
from data.market_result import MarketResult
from engines.indicator_cache import IndicatorCache
from engines.indicator_registry import IndicatorRegistry, build_default_registry
from engines.indicator_result import IndicatorResult
from indicators.base import IndicatorOutput, IndicatorParameterError, has_usable_volume

_logger = get_logger(__name__)

_REQUIRED_COLUMNS = ("open", "high", "low", "close")


class IndicatorRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Indikator-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class IndicatorRules:
    """Geladene Indikator-Regeln.

    Attributes:
        indicators: Zuordnung Indikatorname -> Parameter (inkl. ``enabled``).
        min_candles: Harte Untergrenze an Kerzen für ein gültiges Ergebnis.
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    indicators: dict[str, dict[str, Any]]
    min_candles: int
    version: int


def load_indicator_rules(path: Path | None = None) -> IndicatorRules:
    """Lädt die Indikator-Regeln aus der TOML-Datei.

    Args:
        path: Optionaler Pfad. Standard ist ``knowledge/indicator_rules.toml``.

    Returns:
        Die geladenen :class:`IndicatorRules`.

    Raises:
        IndicatorRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or INDICATOR_RULES_FILE
    if not rules_path.is_file():
        raise IndicatorRulesError(f"Indikator-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise IndicatorRulesError(f"Indikator-Regeln sind kein gültiges TOML: {error}") from error

    indicators = data.get("indicators")
    if not isinstance(indicators, dict) or not indicators:
        raise IndicatorRulesError("Abschnitt [indicators] fehlt oder ist leer.")

    validation = data.get("validation", {})
    meta = data.get("meta", {})
    return IndicatorRules(
        indicators={name: dict(cfg) for name, cfg in indicators.items()},
        min_candles=int(validation.get("min_candles", 1)),
        version=int(meta.get("version", 0)),
    )


class IndicatorEngine:
    """Berechnet technische Indikatoren aus OHLCV-Daten.

    Args:
        rules: Geladene Indikator-Regeln (Parameter, Validierung, Version).
        registry: Registry der Indikatoren. Standard ist die Registry mit allen
            Standard-Indikatoren.
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: IndicatorRules,
        registry: IndicatorRegistry | None = None,
        cache: IndicatorCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls,
        path: Path | None = None,
        cache: IndicatorCache | None = None,
    ) -> IndicatorEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_indicator_rules(path), cache=cache)

    def calculate(
        self, data: pd.DataFrame, symbol: str = "", timeframe: str = "base"
    ) -> IndicatorResult:
        """Berechnet alle aktivierten Indikatoren für einen OHLCV-DataFrame.

        Args:
            data: OHLCV-DataFrame im kanonischen Schema.
            symbol: Symbolname (für Metadaten und Cache-Schlüssel).
            timeframe: Zeitebenen-Label (für Metadaten; MTF ist vorbereitet).

        Returns:
            Das aggregierte :class:`IndicatorResult`.
        """
        cache_key = self._cache_key(data, symbol, timeframe)
        if self._cache is not None and cache_key is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        result = self._calculate(data, symbol, timeframe)
        # Ergebnis ist unveränderlich (frozen): Rechenzeit über einen neuen,
        # ansonsten identischen Wert setzen statt das Objekt zu mutieren.
        result = replace(result, calculation_time=self._timer() - start)

        if self._cache is not None and cache_key is not None:
            self._cache.set(cache_key, result)
        return result

    def calculate_symbol(
        self, market_result: MarketResult, symbol: str, timeframe: str = "base"
    ) -> IndicatorResult:
        """Berechnet Indikatoren für ein Symbol eines :class:`MarketResult`.

        Args:
            market_result: Ergebnis der Data Layer.
            symbol: Zu verarbeitendes Symbol.
            timeframe: Zeitebenen-Label.

        Returns:
            Das :class:`IndicatorResult`. Fehlt das Symbol, ist das Ergebnis
            ungültig und trägt eine entsprechende Warnung.
        """
        frame = market_result.frame(symbol)
        if frame is None:
            return IndicatorResult(
                valid=False,
                warnings=[f"Keine Marktdaten für Symbol '{symbol}'."],
                metadata={"symbol": symbol, "timeframe": timeframe, "candle_count": 0},
            )
        return self.calculate(frame, symbol=symbol, timeframe=timeframe)

    def calculate_all(
        self, market_result: MarketResult, timeframe: str = "base"
    ) -> dict[str, IndicatorResult]:
        """Berechnet Indikatoren für alle Symbole eines :class:`MarketResult`."""
        return {
            symbol: self.calculate(frame, symbol=symbol, timeframe=timeframe)
            for symbol, frame in market_result.data.items()
        }

    def _calculate(self, data: pd.DataFrame, symbol: str, timeframe: str) -> IndicatorResult:
        """Kern der Berechnung inkl. Validierung (ohne Zeitmessung/Cache).

        Sammelt Ausgaben/Warnungen/Gültigkeit in lokalen Akkumulatoren und
        konstruiert das unveränderliche :class:`IndicatorResult` **einmalig** am
        Ende – es wird nach seiner Erstellung nicht mehr verändert.
        """
        candle_count = len(data)
        metadata: dict[str, Any] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candle_count": candle_count,
            "rules_version": self._rules.version,
        }
        warnings: list[str] = []
        outputs: dict[str, IndicatorOutput] = {}
        valid = True

        missing_columns = [c for c in _REQUIRED_COLUMNS if c not in data.columns]
        if missing_columns:
            warnings.append(f"Fehlende Pflichtspalten: {', '.join(missing_columns)}.")
            return IndicatorResult(valid=False, warnings=warnings, metadata=metadata)

        if candle_count < self._rules.min_candles:
            valid = False
            warnings.append(
                f"Zu wenig Historie: {candle_count} Kerzen (< {self._rules.min_candles})."
            )
        if data["close"].isna().any():
            warnings.append("NaN in Schlusskursen entdeckt.")

        volume_ok = has_usable_volume(data)
        for name, cfg in self._rules.indicators.items():
            if not self._run_indicator(name, cfg, data, candle_count, volume_ok, outputs, warnings):
                valid = False

        metadata["computed"] = list(outputs)
        return IndicatorResult(outputs=outputs, valid=valid, warnings=warnings, metadata=metadata)

    def _run_indicator(
        self,
        name: str,
        cfg: dict[str, Any],
        data: pd.DataFrame,
        candle_count: int,
        volume_ok: bool,
        outputs: dict[str, IndicatorOutput],
        warnings: list[str],
    ) -> bool:
        """Berechnet einen einzelnen Indikator und ergänzt die Akkumulatoren.

        Returns:
            ``False``, wenn der Indikator das Gesamtergebnis ungültig macht
            (ungültige Parameter), sonst ``True``.
        """
        if not cfg.get("enabled", False):
            return True
        if name not in self._registry:
            warnings.append(f"Indikator '{name}' ist nicht registriert.")
            return True

        indicator = self._registry.get(name)
        params = {key: value for key, value in cfg.items() if key != "enabled"}

        if indicator.requires_volume and not volume_ok:
            warnings.append(f"Fehlende Volumendaten – '{name}' übersprungen.")
            return True
        try:
            min_needed = indicator.min_candles(params)
        except IndicatorParameterError as error:
            warnings.append(str(error))
            return False
        if candle_count < min_needed:
            warnings.append(
                f"Zu wenig Historie für '{name}' ({candle_count} < {min_needed}) – übersprungen."
            )
            return True

        try:
            output = indicator.compute(data, params)
        except Exception as error:  # Rechenfehler eines Indikators isoliert behandeln.
            _logger.warning("Indikator '%s' fehlgeschlagen: %s", name, error)
            warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
            return True

        outputs[name] = output
        warnings.extend(output.warnings)
        return True

    def _cache_key(self, data: pd.DataFrame, symbol: str, timeframe: str) -> str | None:
        """Bildet einen stabilen Cache-Schlüssel oder ``None`` (leere Daten)."""
        if data.empty:
            return None
        last_index = data.index[-1]
        last_close = data["close"].iloc[-1] if "close" in data.columns else "na"
        return f"{symbol}|{timeframe}|{len(data)}|{last_index}|{last_close}|{self._rules.version}"
