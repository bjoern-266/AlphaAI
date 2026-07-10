"""Recommendation Engine – die letzte fachliche Entscheidungsschicht.

Die :class:`RecommendationEngine` kombiniert
:class:`~engines.strategy_result.StrategyReport`,
:class:`~engines.score_result.ScoreReport` und
:class:`~engines.risk_result.RiskReport` je Hypothese zu einer objektiven,
vollständig erklärbaren :class:`~engines.recommendation_result.RecommendationResult`.

Sie eröffnet **keine** Position, sendet **keine** Order und kommuniziert
**nicht** mit Brokern. ``LOW`` und ``REJECT`` sind vollwertige Empfehlungen. Ein
hoher Score allein führt wegen der Faktorgewichte und der No-Trade-Gates **nie**
zu hoher Stärke (HIGH/VERY_HIGH). Richtung (``Direction``) und Stärke
(``RecommendationStrength``) sind vollständig getrennt.

Parameter stammen ausschließlich aus ``knowledge/recommendation_rules.toml``.
Neue Recommendation-Modelle werden nur über die ``RecommendationRegistry``
ergänzt – die Engine bleibt unverändert.
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import RECOMMENDATION_RULES_FILE
from engines.recommendation_cache import RecommendationCache
from engines.recommendation_registry import RecommendationRegistry, build_default_registry
from engines.recommendation_result import (
    Direction,
    RecommendationReport,
    RecommendationResult,
    RecommendationStrength,
    SuggestedAction,
)
from engines.risk_result import RiskReport, RiskResult
from engines.score_result import ScoreReport, ScoreResult
from engines.strategy_result import StrategyReport, StrategyResult
from models.recommendation import RECOMMENDATION_FACTOR_NAMES, RecommendationContext
from recommendation.base import (
    CONFIDENCE_WEIGHT_KEYS,
    RecommendationParameterError,
    action_for_strength,
    clamp_confidence,
    clamp_rating,
    compute_confidence,
    compute_factors,
    compute_overall_rating,
    validate_weights,
)

_logger = get_logger(__name__)


class RecommendationRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Recommendation-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class RecommendationRules:
    """Geladene Recommendation-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter (inkl. ``enabled``).
        factor_weights: Gewichte der sechs Faktoren (Summe 100 %).
        confidence_weights: Gewichte der Confidence (Summe 100 %).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    factor_weights: dict[str, float]
    confidence_weights: dict[str, float]
    consensus_full_at: int
    version: int


_RESERVED_SECTIONS = frozenset({"meta", "weights", "confidence", "factors"})


def load_recommendation_rules(path: Path | None = None) -> RecommendationRules:
    """Lädt die Recommendation-Regeln aus der TOML-Datei.

    Raises:
        RecommendationRulesError: Wenn die Datei fehlt oder strukturell ungültig ist.
    """
    rules_path = path or RECOMMENDATION_RULES_FILE
    if not rules_path.is_file():
        raise RecommendationRulesError(f"Recommendation-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise RecommendationRulesError(
            f"Recommendation-Regeln sind kein gültiges TOML: {error}"
        ) from error

    models = {name: dict(cfg) for name, cfg in data.items() if name not in _RESERVED_SECTIONS}
    if not models:
        raise RecommendationRulesError("Keine Recommendation-Modelle in der Regeldatei definiert.")

    weights_raw = data.get("weights")
    if not isinstance(weights_raw, dict):
        raise RecommendationRulesError("Abschnitt [weights] mit den Faktorgewichten fehlt.")
    confidence_raw = data.get("confidence")
    if not isinstance(confidence_raw, dict):
        raise RecommendationRulesError("Abschnitt [confidence] mit den Gewichten fehlt.")
    try:
        factor_weights = validate_weights(weights_raw, RECOMMENDATION_FACTOR_NAMES, "weights")
        confidence_weights = validate_weights(confidence_raw, CONFIDENCE_WEIGHT_KEYS, "confidence")
    except RecommendationParameterError as error:
        raise RecommendationRulesError(str(error)) from error

    consensus_full_at = int(data.get("factors", {}).get("consensus_full_at", 2))
    if consensus_full_at < 1:
        raise RecommendationRulesError("[factors].consensus_full_at muss mindestens 1 sein.")

    meta = data.get("meta", {})
    return RecommendationRules(
        models=models,
        factor_weights=factor_weights,
        confidence_weights=confidence_weights,
        consensus_full_at=consensus_full_at,
        version=int(meta.get("version", 0)),
    )


class RecommendationEngine:
    """Kombiniert Strategy/Score/Risk zu erklärbaren Empfehlungen.

    Args:
        rules: Geladene Recommendation-Regeln.
        registry: Registry der Modelle (Standard: alle Standardmodelle).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: RecommendationRules,
        registry: RecommendationRegistry | None = None,
        cache: RecommendationCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls, path: Path | None = None, cache: RecommendationCache | None = None
    ) -> RecommendationEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_recommendation_rules(path), cache=cache)

    def recommend(
        self,
        strategy_report: StrategyReport,
        score_report: ScoreReport,
        risk_report: RiskReport,
        symbol: str = "",
        timeframe: str = "base",
    ) -> RecommendationReport:
        """Erzeugt Empfehlungen für alle bewerteten Hypothesen."""
        cache_key = self._cache_key(strategy_report, score_report, risk_report, symbol, timeframe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._recommend(strategy_report, score_report, risk_report, symbol, timeframe)
        # Report ist unveränderlich (frozen): Rechenzeit über eine Kopie setzen.
        report = replace(report, calculation_time=self._timer() - start)

        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _recommend(
        self,
        strategy_report: StrategyReport,
        score_report: ScoreReport,
        risk_report: RiskReport,
        symbol: str,
        timeframe: str,
    ) -> RecommendationReport:
        """Kern der Empfehlung inkl. Validierung (ohne Zeitmessung/Cache)."""
        metadata: dict[str, Any] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "rules_version": self._rules.version,
        }
        warnings: list[str] = []
        results: list[RecommendationResult] = []
        valid = True

        if not strategy_report.valid:
            valid = False
            warnings.append("Ungültiger/fehlender Strategie-Report.")
        if not score_report.valid:
            valid = False
            warnings.append("Ungültiger/fehlender Score-Report.")
        if not risk_report.valid:
            valid = False
            warnings.append("Ungültiger/fehlender Risiko-Report.")
        if not score_report.results:
            warnings.append("Keine Scores zum Empfehlen vorhanden.")
            return RecommendationReport(
                results=results, valid=valid, warnings=warnings, metadata=metadata
            )

        strategies_by_id = {s.hypothesis_id: s for s in strategy_report.results}
        risks_by_hyp = {r.hypothesis_id: r for r in risk_report.results}
        all_strategies = list(strategy_report.results)

        for score_result in score_report.results:
            strategy = strategies_by_id.get(score_result.hypothesis_id)
            risk = risks_by_hyp.get(score_result.hypothesis_id)
            if strategy is None or risk is None:
                valid = False
                warnings.append(
                    f"Fehlende Strategie-/Risiko-Daten zu Hypothese "
                    f"'{score_result.hypothesis_id}' – übersprungen."
                )
                continue
            recommendation, model_ok = self._recommend_one(
                strategy, score_result, risk, all_strategies, symbol, timeframe
            )
            results.append(recommendation)
            if not model_ok:
                valid = False

        metadata["recommended"] = len(results)
        return RecommendationReport(
            results=results, valid=valid, warnings=warnings, metadata=metadata
        )

    def _recommend_one(
        self,
        strategy_result: StrategyResult,
        score_result: ScoreResult,
        risk_result: RiskResult,
        strategies: list[StrategyResult],
        symbol: str,
        timeframe: str,
    ) -> tuple[RecommendationResult, bool]:
        """Erzeugt die Empfehlung einer einzelnen Hypothese über alle Modelle."""
        factors = compute_factors(
            strategy_result,
            score_result,
            risk_result,
            strategies,
            consensus_full_at=self._rules.consensus_full_at,
        )
        overall_rating = compute_overall_rating(factors, self._rules.factor_weights)
        base_confidence = compute_confidence(
            strategy_result, factors, self._rules.confidence_weights
        )
        context = RecommendationContext(
            strategy_result=strategy_result,
            score_result=score_result,
            risk_result=risk_result,
            strategies=strategies,
            factors=factors,
            overall_rating=overall_rating,
            base_confidence=base_confidence,
            symbol=symbol,
            timeframe=timeframe,
        )

        outputs: dict[str, Any] = {}
        warnings: list[str] = []
        valid = True
        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Recommendation-Modell '{name}' ist nicht registriert.")
                continue
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                outputs[name] = self._registry.get(name).compute(context, params)
            except RecommendationParameterError as error:
                valid = False
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Recommendation-Modell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
                continue
            warnings.extend(outputs[name].warnings)

        rating = outputs["decision_model"].value if "decision_model" in outputs else overall_rating
        confidence = (
            outputs["confidence_model"].value if "confidence_model" in outputs else base_confidence
        )

        strength, action, gate_reasons = self._resolve_strength(outputs, warnings)
        direction = context.trade_direction
        rating, confidence, valid = self._validate_outputs(
            rating, confidence, direction, strength, warnings, valid
        )

        reasons = self._collect_reasons(outputs, factors, gate_reasons)
        summary = self._build_summary(outputs, context, direction, strength)

        result = RecommendationResult(
            recommendation_id=f"rec:{score_result.score_id}",
            risk_id=risk_result.risk_id,
            score_id=score_result.score_id,
            hypothesis_id=score_result.hypothesis_id,
            direction=direction,
            recommendation_strength=strength,
            confidence=confidence,
            overall_rating=rating,
            suggested_action=action,
            reasons=reasons,
            warnings=warnings,
            summary=summary,
            metadata={
                "factors": {name: f.value for name, f in factors.items()},
                "model_values": {name: out.value for name, out in outputs.items()},
            },
            timestamp=score_result.timestamp,
        )
        return result, valid

    @staticmethod
    def _resolve_strength(
        outputs: dict[str, Any], warnings: list[str]
    ) -> tuple[RecommendationStrength, SuggestedAction, list[str]]:
        """Ermittelt Stärke/Handlung aus dem Recommendation-Modell (mit Fallback)."""
        if "recommendation_model" not in outputs:
            warnings.append("Kein Recommendation-Modell aktiv – konservativ LOW.")
            return RecommendationStrength.LOW, SuggestedAction.WAIT, []
        details = outputs["recommendation_model"].details
        strength = details.get("strength")
        action = details.get("action")
        gate_reasons = list(outputs["recommendation_model"].reasons)
        if not isinstance(strength, RecommendationStrength):
            warnings.append("Ungültige Empfehlungsstärke – konservativ LOW.")
            return RecommendationStrength.LOW, SuggestedAction.WAIT, gate_reasons
        if not isinstance(action, SuggestedAction):
            action = action_for_strength(strength)
        return strength, action, gate_reasons

    @staticmethod
    def _validate_outputs(
        rating: float,
        confidence: float,
        direction: Direction,
        strength: RecommendationStrength,
        warnings: list[str],
        valid: bool,
    ) -> tuple[float, float, bool]:
        """Prüft Rating (0..100), Confidence (0..1), Richtung und Stärke."""
        if not 0.0 <= rating <= 100.0:
            warnings.append(f"Ungültiges Rating {rating} – begrenzt auf 0..100.")
            rating = clamp_rating(rating)
            valid = False
        if not 0.0 <= confidence <= 1.0:
            warnings.append(f"Ungültige Confidence {confidence} – begrenzt auf 0..1.")
            confidence = clamp_confidence(confidence)
            valid = False
        if not isinstance(direction, Direction):
            warnings.append("Ungültige Richtung.")
            valid = False
        if not isinstance(strength, RecommendationStrength):
            warnings.append("Ungültige Empfehlungsstärke.")
            valid = False
        return rating, confidence, valid

    @staticmethod
    def _collect_reasons(
        outputs: dict[str, Any], factors: dict[str, Any], gate_reasons: list[str]
    ) -> list[str]:
        """Stellt die erklärenden Gründe zusammen (Explanation + Gates)."""
        if "explanation_model" in outputs:
            reasons = list(outputs["explanation_model"].details.get("reasons", []))
        else:
            reasons = [factor.reason for factor in factors.values()]
        reasons.extend(gate_reasons)
        return reasons

    @staticmethod
    def _build_summary(
        outputs: dict[str, Any],
        context: RecommendationContext,
        direction: Direction,
        strength: RecommendationStrength,
    ) -> str:
        """Baut die Zusammenfassung: Richtung und Stärke getrennt vorangestellt."""
        if "summary_model" in outputs:
            body = outputs["summary_model"].details.get("summary", "")
        else:
            body = (
                f"{context.symbol or 'Symbol'} Richtung {direction.value.upper()}, "
                f"Rating {context.overall_rating:.0f}/100."
            )
        return f"{direction.value.upper()} / {strength.value.upper()} — {body}"

    def _cache_key(
        self,
        strategy_report: StrategyReport,
        score_report: ScoreReport,
        risk_report: RiskReport,
        symbol: str,
        timeframe: str,
    ) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        return (
            f"{symbol}|{timeframe}|{strategy_report.hypothesis_count}|"
            f"{score_report.score_count}|{risk_report.risk_count}|{self._rules.version}"
        )
