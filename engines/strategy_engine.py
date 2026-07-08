"""Strategy Engine – kombiniert Indikatoren und Muster zu Hypothesen.

Die :class:`StrategyEngine` nimmt ein
:class:`~engines.indicator_result.IndicatorResult` und einen
:class:`~engines.pattern_result.PatternReport` (plus optionale Rohdaten)
entgegen und liefert einen :class:`~engines.strategy_result.StrategyReport` mit
objektiven **Hypothesen**. Sie trifft **keine** Kauf-/Verkaufsentscheidung und
vergibt **keinen** Gesamtscore.

Parameter stammen ausschließlich aus ``knowledge/strategy_rules.toml``.
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import STRATEGY_RULES_FILE
from engines.indicator_result import IndicatorResult
from engines.pattern_result import PatternReport
from engines.strategy_cache import StrategyCache
from engines.strategy_registry import StrategyRegistry, build_default_registry
from engines.strategy_result import StrategyReport
from strategies.base import StrategyContext, StrategyParameterError

_logger = get_logger(__name__)


class StrategyRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Strategie-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class StrategyRules:
    """Geladene Strategie-Regeln.

    Attributes:
        strategies: Zuordnung Strategiename -> Parameter (inkl. ``enabled``).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    strategies: dict[str, dict[str, Any]]
    version: int


def load_strategy_rules(path: Path | None = None) -> StrategyRules:
    """Lädt die Strategie-Regeln aus der TOML-Datei.

    Raises:
        StrategyRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or STRATEGY_RULES_FILE
    if not rules_path.is_file():
        raise StrategyRulesError(f"Strategie-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise StrategyRulesError(f"Strategie-Regeln sind kein gültiges TOML: {error}") from error

    strategies = data.get("strategies")
    if not isinstance(strategies, dict) or not strategies:
        raise StrategyRulesError("Abschnitt [strategies] fehlt oder ist leer.")

    meta = data.get("meta", {})
    return StrategyRules(
        strategies={name: dict(cfg) for name, cfg in strategies.items()},
        version=int(meta.get("version", 0)),
    )


class StrategyEngine:
    """Erzeugt Handelshypothesen aus Indikatoren und Mustern.

    Args:
        rules: Geladene Strategie-Regeln.
        registry: Registry der Strategien (Standard: alle Standard-Strategien).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: StrategyRules,
        registry: StrategyRegistry | None = None,
        cache: StrategyCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls, path: Path | None = None, cache: StrategyCache | None = None
    ) -> StrategyEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_strategy_rules(path), cache=cache)

    def evaluate(
        self,
        indicators: IndicatorResult,
        patterns: PatternReport,
        data: pd.DataFrame | None = None,
        symbol: str = "",
        timeframe: str = "base",
    ) -> StrategyReport:
        """Wertet alle aktivierten Strategien aus und erzeugt Hypothesen."""
        cache_key = self._cache_key(indicators, patterns, symbol, timeframe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._evaluate(indicators, patterns, data, symbol, timeframe)
        report.calculation_time = self._timer() - start

        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _evaluate(
        self,
        indicators: IndicatorResult,
        patterns: PatternReport,
        data: pd.DataFrame | None,
        symbol: str,
        timeframe: str,
    ) -> StrategyReport:
        """Kern der Auswertung inkl. Validierung (ohne Zeitmessung/Cache)."""
        report = StrategyReport()
        report.metadata.update(
            {"symbol": symbol, "timeframe": timeframe, "rules_version": self._rules.version}
        )

        if not indicators.valid:
            report.valid = False
            report.warnings.append("Ungültige/fehlende Indikatordaten.")
        if not patterns.valid:
            report.valid = False
            report.warnings.append("Ungültige/fehlende Musterdaten.")
        self._check_consistency(indicators, patterns, report)

        context = StrategyContext(
            indicators=indicators,
            patterns=patterns,
            data=data,
            symbol=symbol,
            timeframe=timeframe,
        )
        for name, cfg in self._rules.strategies.items():
            self._run_strategy(name, cfg, context, indicators, patterns, report)

        report.metadata["hypotheses"] = [r.strategy_name for r in report.results]
        report.metadata["bullish"] = len(report.bullish)
        report.metadata["bearish"] = len(report.bearish)
        return report

    def _run_strategy(
        self,
        name: str,
        cfg: dict[str, Any],
        context: StrategyContext,
        indicators: IndicatorResult,
        patterns: PatternReport,
        report: StrategyReport,
    ) -> None:
        """Wertet eine einzelne Strategie aus und ergänzt den Report."""
        if not cfg.get("enabled", False):
            return
        if name not in self._registry:
            report.warnings.append(f"Strategie '{name}' ist nicht registriert.")
            return

        strategy = self._registry.get(name)
        missing_ind = [r for r in strategy.indicator_requirements if r not in indicators.outputs]
        if missing_ind:
            report.warnings.append(
                f"Strategie '{name}' übersprungen: fehlende Indikatoren {missing_ind}."
            )
            return
        missing_pat = [r for r in strategy.pattern_requirements if not patterns.by_name(r)]
        if missing_pat:
            report.warnings.append(
                f"Strategie '{name}' übersprungen: fehlende Muster {missing_pat}."
            )
            return

        params = {key: value for key, value in cfg.items() if key != "enabled"}
        try:
            evaluation = strategy.evaluate(context, params)
        except StrategyParameterError as error:
            report.valid = False
            report.warnings.append(str(error))
            return
        except Exception as error:  # Fehler einer Strategie isoliert behandeln.
            _logger.warning("Strategie '%s' fehlgeschlagen: %s", name, error)
            report.warnings.append(f"Auswertung von '{name}' fehlgeschlagen: {error}")
            return

        report.warnings.extend(evaluation.warnings)
        if evaluation.result is not None:
            report.results.append(evaluation.result)

    @staticmethod
    def _check_consistency(
        indicators: IndicatorResult, patterns: PatternReport, report: StrategyReport
    ) -> None:
        """Meldet inkonsistente Ergebnisse (abweichender Timeframe/Kerzenzahl)."""
        ind_tf = indicators.metadata.get("timeframe")
        pat_tf = patterns.metadata.get("timeframe")
        if ind_tf is not None and pat_tf is not None and ind_tf != pat_tf:
            report.warnings.append(
                f"Inkonsistente Ergebnisse: Timeframe {ind_tf} (Indikatoren) != {pat_tf} (Muster)."
            )
        ind_cc = indicators.metadata.get("candle_count")
        pat_cc = patterns.metadata.get("candle_count")
        if ind_cc is not None and pat_cc is not None and ind_cc != pat_cc:
            report.warnings.append(f"Inkonsistente Ergebnisse: Kerzenzahl {ind_cc} != {pat_cc}.")

    def _cache_key(
        self, indicators: IndicatorResult, patterns: PatternReport, symbol: str, timeframe: str
    ) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        ind_fp = (
            f"{indicators.metadata.get('candle_count')}-{indicators.metadata.get('rules_version')}"
        )
        pat_fp = f"{patterns.pattern_count}-{patterns.metadata.get('rules_version')}"
        return f"{symbol}|{timeframe}|{ind_fp}|{pat_fp}|{self._rules.version}"
