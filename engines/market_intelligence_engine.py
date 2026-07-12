"""Market Intelligence Engine – priorisiert die objektiv besten Chancen.

Die :class:`MarketIntelligenceEngine` bewertet je Aktie die **bereits
vorhandenen** Ergebnisse (Empfehlung, Risiko, Analytics, Backtesting, Paper
Trading) über die registrierten Bewertungsmodelle, fasst sie zu einem
``opportunity_score`` zusammen, ordnet alle Chancen in ein Ranking und erzeugt
daraus Statistik, Herleitungen und Watchlists.

Sie **berechnet keine** neue Handelsregel, verändert **keine** bestehenden
Ergebnisse (Recommendation/Risk/Score/Strategy/Pattern/Indicator/Analytics) und
trifft **keine** Handelsentscheidung. Parameter stammen ausschließlich aus
``knowledge/market_intelligence_rules.toml``. Neue Bewertungsmodelle werden nur
über die ``MarketIntelligenceRegistry`` ergänzt – die Engine bleibt
**unverändert** (Open/Closed).
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core.exceptions import AlphaAIError, MarketIntelligenceParameterError
from core.logging_config import get_logger
from core.paths import MARKET_INTELLIGENCE_RULES_FILE
from engines.market_intelligence_cache import OpportunityCache
from engines.market_intelligence_registry import (
    MarketIntelligenceRegistry,
    build_default_registry,
)
from market_intelligence import ranking, ranking_engine
from market_intelligence.explainer import build_explanations
from market_intelligence.opportunity import build_opportunity
from market_intelligence.statistics import compute_statistics
from models.opportunity import (
    MarketCandidate,
    MarketIntelligenceContext,
    Opportunity,
    OpportunityModelOutput,
    OpportunityReport,
)

_logger = get_logger(__name__)

_RESERVED_SECTIONS = frozenset({"meta", "scoring", "ranking", "watchlist", "statistics", "filters"})
_WEIGHT_TOLERANCE = 1e-6


class MarketIntelligenceRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Market-Intelligence-Regeln fehlen/ungültig sind."""


@dataclass(frozen=True, slots=True)
class MarketIntelligenceRules:
    """Geladene Market-Intelligence-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter (inkl. ``enabled``/``weight``).
        config: Gemeinsame Konfiguration (Score-Grenzen, Ranking, Watchlist, …).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    config: dict[str, Any]
    version: int


def load_market_intelligence_rules(path: Path | None = None) -> MarketIntelligenceRules:
    """Lädt die Market-Intelligence-Regeln aus der TOML-Datei.

    Raises:
        MarketIntelligenceRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or MARKET_INTELLIGENCE_RULES_FILE
    if not rules_path.is_file():
        raise MarketIntelligenceRulesError(f"Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise MarketIntelligenceRulesError(f"Regeln sind kein gültiges TOML: {error}") from error
    return load_market_intelligence_rules_from_dict(data)


def load_market_intelligence_rules_from_dict(data: dict[str, Any]) -> MarketIntelligenceRules:
    """Baut :class:`MarketIntelligenceRules` aus einer geparsten TOML-Struktur.

    Raises:
        MarketIntelligenceRulesError: Wenn die Struktur ungültig ist (u. a. wenn
            die Gewichte der aktivierten Modelle nicht 100 % ergeben).
    """
    models = {name: dict(cfg) for name, cfg in data.items() if name not in _RESERVED_SECTIONS}
    if not models:
        raise MarketIntelligenceRulesError("Keine Bewertungsmodelle in der Regeldatei definiert.")

    enabled_weight = 0.0
    for name, cfg in models.items():
        if not cfg.get("enabled", False):
            continue
        weight = cfg.get("weight")
        if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
            raise MarketIntelligenceRulesError(f"[{name}].weight muss eine Zahl ≥ 0 sein.")
        enabled_weight += float(weight)
    if abs(enabled_weight - 1.0) > _WEIGHT_TOLERANCE:
        raise MarketIntelligenceRulesError(
            f"Die Gewichte der aktivierten Modelle müssen 1.0 ergeben (aktuell {enabled_weight})."
        )

    config: dict[str, Any] = {}
    for section in ("scoring", "ranking", "watchlist", "statistics", "filters"):
        block = data.get(section, {})
        if not isinstance(block, dict):
            raise MarketIntelligenceRulesError(f"Abschnitt [{section}] muss eine Tabelle sein.")
        config.update(block)

    meta = data.get("meta", {})
    return MarketIntelligenceRules(
        models=models, config=config, version=int(meta.get("version", 0))
    )


class MarketIntelligenceEngine:
    """Bewertet Kandidaten und liefert einen priorisierten OpportunityReport.

    Args:
        rules: Geladene Regeln.
        registry: Registry der Bewertungsmodelle (Standard: alle fünf).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: MarketIntelligenceRules,
        registry: MarketIntelligenceRegistry | None = None,
        cache: OpportunityCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls, path: Path | None = None, cache: OpportunityCache | None = None
    ) -> MarketIntelligenceEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_market_intelligence_rules(path), cache=cache)

    def analyze(self, candidates: Sequence[MarketCandidate]) -> OpportunityReport:
        """Bewertet die Kandidaten und liefert einen priorisierten Report."""
        cache_key = self._cache_key(candidates)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._analyze(candidates)
        report = replace(report, calculation_time=self._timer() - start)
        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _analyze(self, candidates: Sequence[MarketCandidate]) -> OpportunityReport:
        """Kern der Bewertung (ohne Zeitmessung/Cache)."""
        warnings: list[str] = []
        valid = True
        if not candidates:
            warnings.append("Keine Kandidaten übergeben – der Report ist leer.")
            valid = False

        opportunities: list[Opportunity] = []
        seen: set[str] = set()
        for candidate in candidates:
            if not candidate.ticker:
                warnings.append("Kandidat ohne Ticker übersprungen.")
                continue
            if candidate.ticker in seen:
                warnings.append(f"Doppelter Ticker '{candidate.ticker}' übersprungen.")
                continue
            seen.add(candidate.ticker)
            opportunity, candidate_warnings = self._evaluate(candidate)
            warnings.extend(candidate_warnings)
            opportunities.append(opportunity)

        criterion = str(self._rules.config.get("default_sort", ranking.SORT_SCORE))
        ranked = ranking_engine.rank(opportunities, criterion)
        statistics = compute_statistics(
            ranked,
            top_sectors=int(self._rules.config.get("stat_top_sectors", 5)),
            top_markets=int(self._rules.config.get("stat_top_markets", 5)),
        )
        explanations = build_explanations(ranked)
        watchlists = ranking_engine.build_watchlists(ranked, self._rules.config)

        return OpportunityReport(
            opportunities=ranked,
            statistics=statistics,
            explanations=explanations,
            watchlists=watchlists,
            valid=valid,
            warnings=warnings,
            metadata={
                "rules_version": self._rules.version,
                "candidate_count": len(candidates),
                "opportunity_count": len(ranked),
                "sort": criterion,
            },
            timestamp=datetime.now(UTC),
        )

    def _evaluate(self, candidate: MarketCandidate) -> tuple[Opportunity, list[str]]:
        """Bewertet eine einzelne Aktie über die registrierten Modelle."""
        warnings: list[str] = []
        if candidate.recommendation is None:
            warnings.append(f"'{candidate.ticker}': keine Empfehlung – wird als Watch geführt.")
        context = MarketIntelligenceContext(candidate=candidate, config=dict(self._rules.config))
        outputs = self._run_models(context, warnings)
        opportunity = build_opportunity(context, outputs)
        return opportunity, warnings

    def _run_models(
        self, context: MarketIntelligenceContext, warnings: list[str]
    ) -> dict[str, OpportunityModelOutput]:
        """Führt alle aktivierten, registrierten Bewertungsmodelle aus."""
        outputs: dict[str, OpportunityModelOutput] = {}
        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Bewertungsmodell '{name}' ist nicht registriert.")
                continue
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                outputs[name] = self._registry.get(name).compute(context, params)
            except MarketIntelligenceParameterError as error:
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Bewertungsmodell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Bewertung von '{name}' fehlgeschlagen: {error}")
                continue
            warnings.extend(outputs[name].warnings)
        return outputs

    def _cache_key(self, candidates: Sequence[MarketCandidate]) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Kandidaten-Fingerabdrücken."""
        fingerprint = "|".join(
            f"{c.ticker}:{getattr(c.recommendation, 'recommendation_id', '')}" for c in candidates
        )
        return f"{len(candidates)}|{fingerprint}|{self._rules.version}"


__all__ = [
    "MarketIntelligenceEngine",
    "MarketIntelligenceRules",
    "MarketIntelligenceRulesError",
    "load_market_intelligence_rules",
    "load_market_intelligence_rules_from_dict",
]
