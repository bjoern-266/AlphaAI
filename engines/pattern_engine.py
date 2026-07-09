"""Pattern Engine – erkennt Chartmuster.

Die :class:`PatternEngine` nimmt Marktdaten (einen OHLCV-DataFrame bzw. ein
:class:`~data.market_result.MarketResult`) entgegen und liefert ein
:class:`~engines.pattern_result.PatternReport`. Sie orchestriert die
registrierten Muster, validiert die Eingabe und cached Ergebnisse optional.
Sie trifft **keine** Handelsentscheidungen, erzeugt **keine** Scores und
**keine** Signale.

Optional kann ein :class:`~engines.indicator_result.IndicatorResult` übergeben
werden (Architektur ``IndicatorResult → PatternEngine``); die aktuellen Muster
arbeiten jedoch auf den rohen OHLCV-Daten. Das Indikator-Ergebnis wird für
spätere, kombinierte Muster in den Metadaten vermerkt.

Parameter stammen ausschließlich aus ``knowledge/pattern_rules.toml``.
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
from core.paths import PATTERN_RULES_FILE
from data.market_result import MarketResult
from engines.indicator_result import IndicatorResult
from engines.pattern_cache import PatternCache
from engines.pattern_registry import PatternRegistry, build_default_registry
from engines.pattern_result import PatternReport
from patterns.base import PatternParameterError, PatternResult

_logger = get_logger(__name__)

_REQUIRED_COLUMNS = ("open", "high", "low", "close")


class PatternRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Muster-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class PatternRules:
    """Geladene Muster-Regeln.

    Attributes:
        patterns: Zuordnung Mustername -> Parameter (inkl. ``enabled``).
        min_candles: Harte Untergrenze an Kerzen für ein gültiges Ergebnis.
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    patterns: dict[str, dict[str, Any]]
    min_candles: int
    version: int


def load_pattern_rules(path: Path | None = None) -> PatternRules:
    """Lädt die Muster-Regeln aus der TOML-Datei.

    Raises:
        PatternRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or PATTERN_RULES_FILE
    if not rules_path.is_file():
        raise PatternRulesError(f"Muster-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise PatternRulesError(f"Muster-Regeln sind kein gültiges TOML: {error}") from error

    patterns = data.get("patterns")
    if not isinstance(patterns, dict) or not patterns:
        raise PatternRulesError("Abschnitt [patterns] fehlt oder ist leer.")

    validation = data.get("validation", {})
    meta = data.get("meta", {})
    return PatternRules(
        patterns={name: dict(cfg) for name, cfg in patterns.items()},
        min_candles=int(validation.get("min_candles", 1)),
        version=int(meta.get("version", 0)),
    )


class PatternEngine:
    """Erkennt Chartmuster aus OHLCV-Daten.

    Args:
        rules: Geladene Muster-Regeln.
        registry: Registry der Muster (Standard: alle Standard-Muster).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: PatternRules,
        registry: PatternRegistry | None = None,
        cache: PatternCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls, path: Path | None = None, cache: PatternCache | None = None
    ) -> PatternEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_pattern_rules(path), cache=cache)

    def detect(
        self,
        data: pd.DataFrame,
        symbol: str = "",
        timeframe: str = "base",
        indicators: IndicatorResult | None = None,
    ) -> PatternReport:
        """Erkennt alle aktivierten Muster für einen OHLCV-DataFrame."""
        cache_key = self._cache_key(data, symbol, timeframe)
        if self._cache is not None and cache_key is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._detect(data, symbol, timeframe, indicators)
        # Report ist unveränderlich (frozen): Rechenzeit über eine Kopie setzen.
        report = replace(report, calculation_time=self._timer() - start)

        if self._cache is not None and cache_key is not None:
            self._cache.set(cache_key, report)
        return report

    def detect_symbol(
        self, market_result: MarketResult, symbol: str, timeframe: str = "base"
    ) -> PatternReport:
        """Erkennt Muster für ein Symbol eines :class:`MarketResult`."""
        frame = market_result.frame(symbol)
        if frame is None:
            return PatternReport(
                valid=False,
                warnings=[f"Keine Marktdaten für Symbol '{symbol}'."],
                metadata={"symbol": symbol, "timeframe": timeframe, "candle_count": 0},
            )
        return self.detect(frame, symbol=symbol, timeframe=timeframe)

    def detect_all(
        self, market_result: MarketResult, timeframe: str = "base"
    ) -> dict[str, PatternReport]:
        """Erkennt Muster für alle Symbole eines :class:`MarketResult`."""
        return {
            symbol: self.detect(frame, symbol=symbol, timeframe=timeframe)
            for symbol, frame in market_result.data.items()
        }

    def _detect(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str,
        indicators: IndicatorResult | None,
    ) -> PatternReport:
        """Kern der Erkennung inkl. Validierung (ohne Zeitmessung/Cache).

        Sammelt Ergebnisse/Warnungen/Gültigkeit lokal und konstruiert den
        unveränderlichen :class:`PatternReport` **einmalig** am Ende.
        """
        candle_count = len(data)
        metadata: dict[str, Any] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candle_count": candle_count,
            "rules_version": self._rules.version,
            "has_indicators": indicators is not None,
        }
        warnings: list[str] = []
        results: list[PatternResult] = []
        valid = True

        missing_columns = [c for c in _REQUIRED_COLUMNS if c not in data.columns]
        if missing_columns:
            warnings.append(f"Fehlende Pflichtspalten: {', '.join(missing_columns)}.")
            return PatternReport(valid=False, warnings=warnings, metadata=metadata)

        if not self._is_valid_series(data):
            valid = False
            warnings.append("Ungültige Zeitreihe (Index nicht eindeutig/sortiert).")
        if candle_count < self._rules.min_candles:
            valid = False
            warnings.append(
                f"Zu wenig Historie: {candle_count} Kerzen (< {self._rules.min_candles})."
            )
        if data["close"].isna().any():
            warnings.append("NaN in Schlusskursen entdeckt.")

        for name, cfg in self._rules.patterns.items():
            if not self._run_pattern(name, cfg, data, candle_count, results, warnings):
                valid = False

        overlaps = self._count_overlaps(results)
        metadata["detected"] = sorted({r.name for r in results})
        metadata["overlapping_patterns"] = overlaps
        if overlaps:
            warnings.append(f"{overlaps} überlappende Muster erkannt.")
        return PatternReport(results=results, valid=valid, warnings=warnings, metadata=metadata)

    def _run_pattern(
        self,
        name: str,
        cfg: dict[str, Any],
        data: pd.DataFrame,
        candle_count: int,
        results: list[PatternResult],
        warnings: list[str],
    ) -> bool:
        """Führt einen einzelnen Muster-Detektor aus und ergänzt die Akkumulatoren.

        Returns:
            ``False``, wenn der Detektor das Gesamtergebnis ungültig macht
            (ungültige Parameter), sonst ``True``.
        """
        if not cfg.get("enabled", False):
            return True
        if name not in self._registry:
            warnings.append(f"Muster '{name}' ist nicht registriert.")
            return True

        pattern = self._registry.get(name)
        if not pattern.implemented:
            warnings.append(f"Muster '{name}' ist vorbereitet, aber nicht implementiert.")
            return True

        params = {key: value for key, value in cfg.items() if key != "enabled"}
        try:
            min_needed = pattern.min_candles(params)
        except PatternParameterError as error:
            warnings.append(str(error))
            return False
        if candle_count < min_needed:
            warnings.append(
                f"Zu wenig Historie für '{name}' ({candle_count} < {min_needed}) – übersprungen."
            )
            return True

        try:
            detection = pattern.detect(data, params)
        except Exception as error:  # Fehler eines Detektors isoliert behandeln.
            _logger.warning("Muster '%s' fehlgeschlagen: %s", name, error)
            warnings.append(f"Erkennung von '{name}' fehlgeschlagen: {error}")
            return True

        results.extend(detection.patterns)
        warnings.extend(detection.warnings)
        return True

    @staticmethod
    def _is_valid_series(data: pd.DataFrame) -> bool:
        """Prüft, ob der Index eindeutig und aufsteigend sortiert ist."""
        index = data.index
        return bool(index.is_unique and index.is_monotonic_increasing)

    @staticmethod
    def _count_overlaps(results: list[PatternResult]) -> int:
        """Zählt überlappende FVG-Zonen (gleiche Preisbereiche überschneiden sich)."""
        zones = [
            (r.metadata["gap_bottom"], r.metadata["gap_top"])
            for r in results
            if r.name == "fvg" and "gap_bottom" in r.metadata
        ]
        zones.sort()
        overlaps = 0
        for earlier, later in zip(zones, zones[1:], strict=False):
            if later[0] < earlier[1]:
                overlaps += 1
        return overlaps

    def _cache_key(self, data: pd.DataFrame, symbol: str, timeframe: str) -> str | None:
        """Bildet einen stabilen Cache-Schlüssel oder ``None`` (leere Daten)."""
        if data.empty:
            return None
        last_index = data.index[-1]
        last_close = data["close"].iloc[-1] if "close" in data.columns else "na"
        return f"{symbol}|{timeframe}|{len(data)}|{last_index}|{last_close}|{self._rules.version}"
