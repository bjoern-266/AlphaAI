"""Score Engine – bewertet jede Hypothese objektiv.

Die :class:`ScoreEngine` nimmt einen
:class:`~engines.strategy_result.StrategyReport` (plus die zugrunde liegenden
Indikator- und Muster-Ergebnisse für die Komponenten) entgegen und liefert
einen :class:`~engines.score_result.ScoreReport`. Sie berechnet **ausschließlich
Scores** – keine Kauf-/Verkaufsentscheidung, keine Positionsgröße, kein Risiko.

Jeder Score ist über seine acht Komponenten vollständig erklärbar. Gewichte
stammen ausschließlich aus ``knowledge/score_rules.toml``.
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import SCORE_RULES_FILE
from engines.indicator_result import IndicatorResult
from engines.pattern_result import PatternReport
from engines.score_cache import ScoreCache
from engines.score_registry import ScoreRegistry, build_default_registry
from engines.score_result import ScoreReport, ScoreResult
from engines.strategy_result import StrategyReport
from scores.base import ScoreContext, ScoreParameterError, compute_components

_logger = get_logger(__name__)

# Zuordnung bekannter Modellnamen zu den benannten ScoreResult-Feldern. Neue
# Modelle erscheinen zusätzlich in metadata['model_scores'], ohne dass die
# Engine geändert werden muss.
_FIELD_MODELS = {
    "total_score": "weighted_score",
    "confidence": "confidence_score",
    "quality_score": "quality_score",
    "consensus_score": "consensus_score",
    "market_score": "market_score",
}


class ScoreRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Score-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class ScoreRules:
    """Geladene Score-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter/Gewichte (inkl. ``enabled``).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    version: int


def load_score_rules(path: Path | None = None) -> ScoreRules:
    """Lädt die Score-Regeln aus der TOML-Datei.

    Raises:
        ScoreRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or SCORE_RULES_FILE
    if not rules_path.is_file():
        raise ScoreRulesError(f"Score-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise ScoreRulesError(f"Score-Regeln sind kein gültiges TOML: {error}") from error

    meta = data.get("meta", {})
    models = {name: dict(cfg) for name, cfg in data.items() if name != "meta"}
    if not models:
        raise ScoreRulesError("Keine Score-Modelle in der Regeldatei definiert.")
    return ScoreRules(models=models, version=int(meta.get("version", 0)))


class ScoreEngine:
    """Bewertet Hypothesen objektiv anhand konfigurierter Score-Modelle.

    Args:
        rules: Geladene Score-Regeln.
        registry: Registry der Score-Modelle (Standard: alle Standardmodelle).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: ScoreRules,
        registry: ScoreRegistry | None = None,
        cache: ScoreCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(cls, path: Path | None = None, cache: ScoreCache | None = None) -> ScoreEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_score_rules(path), cache=cache)

    def score(
        self,
        strategy_report: StrategyReport,
        indicators: IndicatorResult,
        patterns: PatternReport,
        symbol: str = "",
        timeframe: str = "base",
    ) -> ScoreReport:
        """Bewertet alle Hypothesen des Strategie-Reports."""
        cache_key = self._cache_key(strategy_report, indicators, patterns, symbol, timeframe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._score(strategy_report, indicators, patterns, symbol, timeframe)
        report.calculation_time = self._timer() - start

        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _score(
        self,
        strategy_report: StrategyReport,
        indicators: IndicatorResult,
        patterns: PatternReport,
        symbol: str,
        timeframe: str,
    ) -> ScoreReport:
        """Kern der Bewertung inkl. Validierung (ohne Zeitmessung/Cache)."""
        report = ScoreReport()
        report.metadata.update(
            {"symbol": symbol, "timeframe": timeframe, "rules_version": self._rules.version}
        )

        if not strategy_report.valid:
            report.valid = False
            report.warnings.append("Ungültiger/fehlender Strategie-Report.")
        if not strategy_report.results:
            report.warnings.append("Keine Hypothesen zum Bewerten vorhanden.")
            return report

        hypotheses = strategy_report.results
        for hypothesis in hypotheses:
            report.results.append(
                self._score_hypothesis(
                    hypothesis, hypotheses, indicators, patterns, symbol, timeframe, report
                )
            )

        report.metadata["scored"] = report.score_count
        return report

    def _score_hypothesis(
        self,
        hypothesis: ScoreResult | Any,
        hypotheses: list[Any],
        indicators: IndicatorResult,
        patterns: PatternReport,
        symbol: str,
        timeframe: str,
        report: ScoreReport,
    ) -> ScoreResult:
        """Bewertet eine einzelne Hypothese über alle aktivierten Modelle."""
        components = compute_components(hypothesis, indicators, patterns)
        context = ScoreContext(
            strategy_result=hypothesis,
            indicators=indicators,
            patterns=patterns,
            hypotheses=hypotheses,
            components=components,
            symbol=symbol,
            timeframe=timeframe,
        )

        model_scores: dict[str, float] = {}
        reasons: list[str] = [cs.reason for cs in components.values()]
        warnings: list[str] = []

        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Score-Modell '{name}' ist nicht registriert.")
                continue
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                output = self._registry.get(name).compute(context, params)
            except ScoreParameterError as error:
                report.valid = False
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Score-Modell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
                continue
            model_scores[name] = output.value
            reasons.extend(f"[{name}] {reason}" for reason in output.reasons)
            warnings.extend(output.warnings)

        fields = {field: model_scores.get(model, 0.0) for field, model in _FIELD_MODELS.items()}
        return ScoreResult(
            score_id=f"score:{hypothesis.hypothesis_id}",
            strategy_name=hypothesis.strategy_name,
            hypothesis_id=hypothesis.hypothesis_id,
            total_score=fields["total_score"],
            confidence=fields["confidence"],
            quality_score=fields["quality_score"],
            consensus_score=fields["consensus_score"],
            market_score=fields["market_score"],
            component_scores={name: cs.value for name, cs in components.items()},
            reasons=reasons,
            warnings=warnings,
            metadata={"model_scores": model_scores},
            timestamp=hypothesis.timestamp,
        )

    def _cache_key(
        self,
        strategy_report: StrategyReport,
        indicators: IndicatorResult,
        patterns: PatternReport,
        symbol: str,
        timeframe: str,
    ) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        ind_fp = indicators.metadata.get("candle_count")
        pat_fp = patterns.pattern_count
        return (
            f"{symbol}|{timeframe}|{strategy_report.hypothesis_count}|"
            f"{ind_fp}|{pat_fp}|{self._rules.version}"
        )
