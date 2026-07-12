"""Market Discovery Engine – durchsucht den Markt selbstständig.

Die :class:`MarketDiscoveryEngine` lädt automatisch das konfigurierte Universum,
filtert ungeeignete Kandidaten **vor** der vollständigen Analyse, beschafft je Wert
die **bereits vorhandenen** Ergebnisse (über eine injizierte Quelle), reicht sie an
den bestehenden Market-Intelligence-Schritt weiter, gleicht die Ergebnisliste nach
Branchen aus und baut daraus einen priorisierten
:class:`~models.market_discovery.DiscoveryReport`.

Sie **berechnet niemals** Indikatoren, Muster, Strategien, Scores, Risiken oder
Empfehlungen und **verändert** keine bestehende Engine. Parameter stammen
ausschließlich aus ``knowledge/market_discovery_rules.toml``. Neue Märkte werden
nur über die ``MarketDiscoveryRegistry`` ergänzt – die Engine bleibt
**unverändert** (Open/Closed).
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import MARKET_DISCOVERY_RULES_FILE
from engines.market_discovery_cache import DiscoveryCache
from engines.market_discovery_registry import (
    MarketDiscoveryRegistry,
    build_default_registry,
)
from engines.market_intelligence_engine import MarketIntelligenceEngine
from market_discovery.candidate_filter import load_candidate_filter
from market_discovery.discovery_engine import (
    AnalysisProvider,
    IntelligenceEngine,
    empty_analysis_provider,
    run_discovery,
)
from market_discovery.sector_balancer import load_balance_config
from market_discovery.universe_loader import SymbolSource, UniverseLoader, empty_symbol_source
from models.market_discovery import DiscoveryReport

_logger = get_logger(__name__)

_SECTIONS = ("universe", "filter", "balancing", "statistics", "discovery")


class MarketDiscoveryRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Market-Discovery-Regeln fehlen/ungültig sind."""


@dataclass(frozen=True, slots=True)
class MarketDiscoveryRules:
    """Geladene Market-Discovery-Regeln.

    Attributes:
        universe: Universum-Parameter (u. a. ``default_markets``).
        filter: Vorfilter-Grenzwerte.
        balancing: Branchen-Ausgleich.
        statistics: Statistik-Parameter (Top-Anzahlen).
        discovery: Anzeige-Parameter (u. a. ``top_opportunities``).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    universe: dict[str, Any]
    filter: dict[str, Any]
    balancing: dict[str, Any]
    statistics: dict[str, Any]
    discovery: dict[str, Any]
    version: int


def load_market_discovery_rules(path: Path | None = None) -> MarketDiscoveryRules:
    """Lädt die Market-Discovery-Regeln aus der TOML-Datei.

    Raises:
        MarketDiscoveryRulesError: Wenn die Datei fehlt oder ungültig ist.
    """
    rules_path = path or MARKET_DISCOVERY_RULES_FILE
    if not rules_path.is_file():
        raise MarketDiscoveryRulesError(f"Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise MarketDiscoveryRulesError(f"Regeln sind kein gültiges TOML: {error}") from error
    return load_market_discovery_rules_from_dict(data)


def load_market_discovery_rules_from_dict(data: dict[str, Any]) -> MarketDiscoveryRules:
    """Baut :class:`MarketDiscoveryRules` aus einer geparsten TOML-Struktur.

    Raises:
        MarketDiscoveryRulesError: Wenn eine Sektion strukturell ungültig ist.
    """
    sections: dict[str, dict[str, Any]] = {}
    for section in _SECTIONS:
        block = data.get(section, {})
        if not isinstance(block, dict):
            raise MarketDiscoveryRulesError(f"Abschnitt [{section}] muss eine Tabelle sein.")
        sections[section] = dict(block)

    markets = sections["universe"].get("default_markets", [])
    if not isinstance(markets, list):
        raise MarketDiscoveryRulesError("[universe].default_markets muss eine Liste sein.")

    meta = data.get("meta", {})
    return MarketDiscoveryRules(
        universe=sections["universe"],
        filter=sections["filter"],
        balancing=sections["balancing"],
        statistics=sections["statistics"],
        discovery=sections["discovery"],
        version=int(meta.get("version", 0)),
    )


class MarketDiscoveryEngine:
    """Durchsucht das konfigurierte Universum und liefert einen DiscoveryReport.

    Args:
        rules: Geladene Regeln.
        registry: Registry der Märkte (Standard: alle unterstützten Märkte).
        intelligence: Der (bestehende) Market-Intelligence-Schritt (injizierbar).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: MarketDiscoveryRules,
        registry: MarketDiscoveryRegistry | None = None,
        intelligence: IntelligenceEngine | None = None,
        cache: DiscoveryCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._intelligence = intelligence or MarketIntelligenceEngine.from_config()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls,
        path: Path | None = None,
        intelligence: IntelligenceEngine | None = None,
        cache: DiscoveryCache | None = None,
    ) -> MarketDiscoveryEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_market_discovery_rules(path), intelligence=intelligence, cache=cache)

    @property
    def registry(self) -> MarketDiscoveryRegistry:
        """Die Markt-Registry (für Navigation/Verfügbarkeit)."""
        return self._registry

    def discover(
        self,
        markets: Sequence[str] | None = None,
        symbol_source: SymbolSource = empty_symbol_source,
        analysis_provider: AnalysisProvider = empty_analysis_provider,
    ) -> DiscoveryReport:
        """Durchsucht die Märkte und liefert einen priorisierten Report.

        Args:
            markets: Zu durchsuchende Markt-Schlüssel (Standard: ``default_markets``).
            symbol_source: Injizierte Quelle der Werte je Markt.
            analysis_provider: Injizierte Quelle der **vorhandenen** Ergebnisse je Wert.
        """
        requested = (
            list(markets)
            if markets is not None
            else list(self._rules.universe.get("default_markets", []))
        )
        loader = UniverseLoader(self._registry, symbol_source)
        universe, warnings = loader.load(requested)

        cache_key = self._cache_key(universe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = run_discovery(
            universe=universe,
            candidate_filter=load_candidate_filter(self._rules.filter),
            analysis_provider=analysis_provider,
            intelligence=self._intelligence,
            balance_config=load_balance_config(self._rules.balancing),
            top_sectors=int(self._rules.statistics.get("top_sectors", 5)),
            top_markets=int(self._rules.statistics.get("top_markets", 5)),
            warnings=warnings,
        )
        report = replace(
            report,
            calculation_time=self._timer() - start,
            metadata={**report.metadata, "rules_version": self._rules.version},
        )
        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _cache_key(self, universe) -> str:  # noqa: ANN001 - interner Fingerabdruck
        """Bildet einen stabilen Cache-Schlüssel aus dem Universum-Fingerabdruck."""
        tickers = "|".join(universe.tickers())
        return f"{','.join(universe.markets)}|{universe.size}|{tickers}|{self._rules.version}"


__all__ = [
    "MarketDiscoveryEngine",
    "MarketDiscoveryRules",
    "MarketDiscoveryRulesError",
    "load_market_discovery_rules",
    "load_market_discovery_rules_from_dict",
]
