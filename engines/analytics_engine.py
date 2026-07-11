"""Analytics Engine – wertet bestehende Ergebnisse zu Statistiken aus.

Die :class:`AnalyticsEngine` normalisiert die Trades aus einem
:class:`~models.backtest.BacktestReport` und/oder einem
:class:`~models.paper_trading.PaperTradingReport`, führt die registrierten
Analysemodelle darüber aus und fügt die Ergebnisse zu einem
:class:`~models.analytics.AnalyticsReport` zusammen. Sie **bewertet** keine
Trades, verändert **keine** bestehenden Ergebnisse, trifft **keine**
Handelsentscheidung und erzeugt **keine** neuen Empfehlungen – ausschließlich
objektive Statistiken.

Parameter stammen ausschließlich aus ``knowledge/analytics_rules.toml``. Neue
Analysemodelle werden nur über die ``AnalyticsRegistry`` ergänzt – die Engine
bleibt **unverändert** (Open/Closed).
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from analytics import normalization
from analytics.base import AnalyticsParameterError
from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import ANALYTICS_RULES_FILE
from engines.analytics_cache import AnalyticsCache
from engines.analytics_registry import AnalyticsRegistry, build_default_registry
from models.analytics import (
    AnalyticsContext,
    AnalyticsModelOutput,
    AnalyticsReport,
    AnalyticsResult,
    AnalyticsTrade,
    GroupStatistics,
)
from models.backtest import BacktestReport
from models.paper_trading import PaperTradingReport

_logger = get_logger(__name__)

_RESERVED_SECTIONS = frozenset({"meta", "analysis"})
_EMPTY_GROUP = GroupStatistics(label="overall")


class AnalyticsRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Analytics-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class AnalyticsRules:
    """Geladene Analytics-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter (inkl. ``enabled``).
        config: Gemeinsame Analyse-Konfiguration (Bucket-/Label-Parameter).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    config: dict[str, Any]
    version: int


def load_analytics_rules(path: Path | None = None) -> AnalyticsRules:
    """Lädt die Analytics-Regeln aus der TOML-Datei.

    Raises:
        AnalyticsRulesError: Wenn die Datei fehlt oder strukturell ungültig ist.
    """
    rules_path = path or ANALYTICS_RULES_FILE
    if not rules_path.is_file():
        raise AnalyticsRulesError(f"Analytics-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise AnalyticsRulesError(f"Analytics-Regeln sind kein gültiges TOML: {error}") from error
    return load_analytics_rules_from_dict(data)


def load_analytics_rules_from_dict(data: dict[str, Any]) -> AnalyticsRules:
    """Baut :class:`AnalyticsRules` aus einer bereits geparsten TOML-Struktur.

    Raises:
        AnalyticsRulesError: Wenn die Struktur ungültig ist.
    """
    models = {name: dict(cfg) for name, cfg in data.items() if name not in _RESERVED_SECTIONS}
    if not models:
        raise AnalyticsRulesError("Keine Analysemodelle in der Regeldatei definiert.")
    config_raw = data.get("analysis", {})
    if not isinstance(config_raw, dict):
        raise AnalyticsRulesError("Abschnitt [analysis] muss eine Tabelle sein.")
    base_capital = config_raw.get("base_capital", 10000.0)
    if not isinstance(base_capital, (int, float)) or base_capital <= 0:
        raise AnalyticsRulesError("[analysis].base_capital muss größer als 0 sein.")
    meta = data.get("meta", {})
    return AnalyticsRules(
        models=models, config=dict(config_raw), version=int(meta.get("version", 0))
    )


class AnalyticsEngine:
    """Wertet Backtest-/Paper-Trading-Ergebnisse zu einem AnalyticsReport aus.

    Args:
        rules: Geladene Analytics-Regeln.
        registry: Registry der Analysemodelle (Standard: alle Standardmodelle).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: AnalyticsRules,
        registry: AnalyticsRegistry | None = None,
        cache: AnalyticsCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls, path: Path | None = None, cache: AnalyticsCache | None = None
    ) -> AnalyticsEngine:
        """Erzeugt eine Engine mit Regeln aus der Konfigurationsdatei."""
        return cls(rules=load_analytics_rules(path), cache=cache)

    def analyze(
        self,
        backtest_report: BacktestReport | None = None,
        paper_report: PaperTradingReport | None = None,
        symbol: str = "",
        timeframe: str = "base",
    ) -> AnalyticsReport:
        """Analysiert die übergebenen Reports und liefert einen AnalyticsReport."""
        cache_key = self._cache_key(backtest_report, paper_report, symbol, timeframe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._analyze(backtest_report, paper_report, symbol, timeframe)
        report = replace(report, calculation_time=self._timer() - start)
        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _analyze(
        self,
        backtest_report: BacktestReport | None,
        paper_report: PaperTradingReport | None,
        symbol: str,
        timeframe: str,
    ) -> AnalyticsReport:
        """Kern der Analyse (ohne Zeitmessung/Cache)."""
        warnings: list[str] = []
        valid = True
        if backtest_report is None and paper_report is None:
            warnings.append("Weder Backtest- noch Paper-Trading-Report übergeben.")
            valid = False

        trades = normalization.normalize(backtest_report, paper_report)
        if not trades:
            warnings.append("Keine Trades in den Reports – Statistiken sind leer/neutral.")

        backtest_id = _backtest_id(backtest_report)
        paper_id = _paper_id(paper_report)
        journal = list(paper_report.journal) if paper_report is not None else []
        context = AnalyticsContext(
            trades=trades,
            journal=journal,
            backtest_id=backtest_id,
            paper_trading_id=paper_id,
            symbol=symbol,
            timeframe=timeframe,
            config=dict(self._rules.config),
        )

        outputs, model_warnings, model_ok = self._run_models(context)
        warnings.extend(model_warnings)
        result = self._assemble_result(context, outputs, warnings)

        return AnalyticsReport(
            result=result,
            model_outputs=outputs,
            valid=valid and model_ok,
            warnings=warnings,
            metadata={
                "symbol": symbol,
                "timeframe": timeframe,
                "rules_version": self._rules.version,
                "trade_count": len(trades),
            },
        )

    def _run_models(
        self, context: AnalyticsContext
    ) -> tuple[dict[str, AnalyticsModelOutput], list[str], bool]:
        """Führt alle aktivierten, registrierten Analysemodelle aus."""
        outputs: dict[str, AnalyticsModelOutput] = {}
        warnings: list[str] = []
        valid = True
        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Analysemodell '{name}' ist nicht registriert.")
                continue
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                outputs[name] = self._registry.get(name).compute(context, params)
            except AnalyticsParameterError as error:
                valid = False
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Analysemodell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
                continue
            warnings.extend(outputs[name].warnings)
        return outputs, warnings, valid

    def _assemble_result(
        self,
        context: AnalyticsContext,
        outputs: dict[str, AnalyticsModelOutput],
        warnings: list[str],
    ) -> AnalyticsResult:
        """Baut das AnalyticsResult aus den Modell-Ausgaben zusammen."""
        ts = outputs.get("trade_statistics")
        metrics = ts.metrics if ts else {}
        overall = ts.statistics.get("overall", _EMPTY_GROUP) if ts else _EMPTY_GROUP
        long_stats = ts.statistics.get("long", _empty("long")) if ts else _empty("long")
        short_stats = ts.statistics.get("short", _empty("short")) if ts else _empty("short")

        summary = ""
        if "summary_analysis" in outputs:
            summary = str(outputs["summary_analysis"].details.get("summary", ""))

        analytics_id = f"analytics:{context.backtest_id or 'na'}:{context.paper_trading_id or 'na'}"
        return AnalyticsResult(
            analytics_id=analytics_id,
            backtest_id=context.backtest_id,
            paper_trading_id=context.paper_trading_id,
            trade_count=len(context.trades),
            win_rate=metrics.get("win_rate", overall.win_rate),
            loss_rate=metrics.get("loss_rate", overall.loss_rate),
            profit_factor=metrics.get("profit_factor", overall.profit_factor),
            expectancy=metrics.get("expectancy", 0.0),
            average_winner=metrics.get("average_winner", overall.average_winner),
            average_loser=metrics.get("average_loser", overall.average_loser),
            maximum_drawdown=metrics.get("maximum_drawdown", overall.maximum_drawdown),
            average_holding_time=metrics.get("average_holding_time", overall.average_holding_time),
            average_risk_reward=metrics.get("average_risk_reward", 0.0),
            long_statistics=long_stats,
            short_statistics=short_stats,
            strategy_statistics=_stat(outputs, "strategy_analysis", "strategy"),
            pattern_statistics=_stat(outputs, "pattern_analysis", "pattern"),
            recommendation_statistics=_stat(
                outputs, "recommendation_analysis", "recommendation_strength"
            ),
            risk_statistics=_stat(outputs, "risk_analysis", "risk_level"),
            market_statistics=_market_stats(outputs),
            time_statistics=_time_stats(outputs),
            journal_statistics=_journal_stats(outputs),
            performance=(
                outputs["performance_analyzer"].metrics if "performance_analyzer" in outputs else {}
            ),
            summary=summary,
            warnings=list(warnings),
            metadata={"model_metrics": {name: out.metrics for name, out in outputs.items()}},
            timestamp=datetime.now(UTC),
        )

    def _cache_key(
        self,
        backtest_report: BacktestReport | None,
        paper_report: PaperTradingReport | None,
        symbol: str,
        timeframe: str,
    ) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        bt = _backtest_id(backtest_report)
        bt_trades = sum(len(r.trades) for r in backtest_report.results) if backtest_report else 0
        pt = _paper_id(paper_report)
        pt_trades = len(paper_report.closed_results) if paper_report else 0
        return f"{symbol}|{timeframe}|{bt}:{bt_trades}|{pt}:{pt_trades}|{self._rules.version}"


def _empty(label: str) -> GroupStatistics:
    """Leere Gruppenstatistik mit gegebenem Label."""
    return GroupStatistics(label=label)


def _stat(
    outputs: dict[str, AnalyticsModelOutput], model: str, key: str
) -> dict[str, GroupStatistics]:
    """Liest eine Gruppen-Statistik aus einem Modell (mit leerem Fallback)."""
    if model not in outputs:
        return {}
    value = outputs[model].statistics.get(key, {})
    return value if isinstance(value, dict) else {}


def _market_stats(outputs: dict[str, AnalyticsModelOutput]) -> dict[str, GroupStatistics]:
    """Fasst die Marktdimensionen zu einer flachen Statistik zusammen (Präfix)."""
    if "market_analysis" not in outputs:
        return {}
    flat: dict[str, GroupStatistics] = {}
    for dimension, groups in outputs["market_analysis"].statistics.items():
        if isinstance(groups, dict):
            for label, stat in groups.items():
                flat[f"{dimension}:{label}"] = stat
    return flat


def _time_stats(
    outputs: dict[str, AnalyticsModelOutput],
) -> dict[str, dict[str, GroupStatistics]]:
    """Liest die Zeit-Statistiken (verschachtelt) aus dem Modell."""
    if "time_analysis" not in outputs:
        return {}
    return {
        dimension: groups
        for dimension, groups in outputs["time_analysis"].statistics.items()
        if isinstance(groups, dict)
    }


def _journal_stats(outputs: dict[str, AnalyticsModelOutput]) -> dict[str, Any]:
    """Liest die Journal-Statistik aus dem Modell."""
    if "journal_analysis" not in outputs:
        return {}
    value = outputs["journal_analysis"].statistics.get("journal", {})
    return value if isinstance(value, dict) else {}


def _backtest_id(report: BacktestReport | None) -> str:
    """Ermittelt einen Bezeichner des Backtest-Reports (erstes Ergebnis)."""
    if report is None or not report.results:
        return ""
    return report.results[0].backtest_id


def _paper_id(report: PaperTradingReport | None) -> str:
    """Ermittelt einen Bezeichner des Paper-Trading-Reports (Metadata/Ergebnis)."""
    if report is None:
        return ""
    symbol = report.metadata.get("symbol", "")
    return f"paper:{symbol}" if symbol else "paper"


__all__ = [
    "AnalyticsEngine",
    "AnalyticsRules",
    "AnalyticsRulesError",
    "load_analytics_rules",
    "load_analytics_rules_from_dict",
    "AnalyticsTrade",
]
