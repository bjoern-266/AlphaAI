"""Paper Trading Engine – bewertet Empfehlungen mit einem simulierten Portfolio.

Die :class:`PaperTradingEngine` verbindet den Paper Runner (führt die
**bestehende** Pipeline tagweise aus und pflegt ein simuliertes
:class:`~paper_trading.portfolio.PaperPortfolio`) mit den Paper-Trading-Modellen
zu einem :class:`~models.paper_trading.PaperTradingReport`. Sie führt **niemals**
echte Orders aus, verändert **keine** Empfehlung und **keine** Engine, und es gibt
**keine** Broker-Anbindung. Konto- und Risikoeinstellungen stammen ausschließlich
aus ``config/settings.toml`` (über die bestehende Risk Engine).

Parameter des Paper Tradings stammen ausschließlich aus
``knowledge/paper_trading_rules.toml``. Neue Modelle werden nur über die
``PaperTradingRegistry`` ergänzt – die Engine bleibt unverändert.
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import PAPER_TRADING_RULES_FILE
from engines.paper_trading_cache import PaperTradingCache
from engines.paper_trading_registry import PaperTradingRegistry, build_default_registry
from models.market import COL_CLOSE, COL_HIGH, COL_LOW, MarketResult
from models.paper_trading import (
    PaperPerformance,
    PaperPosition,
    PaperStatistics,
    PaperTradingContext,
    PaperTradingModelOutput,
    PaperTradingReport,
    PaperTradingResult,
)
from paper_trading import trade as trade_mod
from paper_trading.base import PaperTradingParameterError
from paper_trading.paper_runner import PaperRunner, PaperRunnerParams
from paper_trading.portfolio import PaperPortfolio
from pipeline.runner import IntegrationRunner

_logger = get_logger(__name__)

_RESERVED_SECTIONS = frozenset({"meta", "runner"})


class PaperTradingRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Paper-Trading-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class PaperTradingRules:
    """Geladene Paper-Trading-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter (inkl. ``enabled``).
        runner: Parameter des Paper Runners.
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    runner: PaperRunnerParams
    version: int


def load_paper_trading_rules(path: Path | None = None) -> PaperTradingRules:
    """Lädt die Paper-Trading-Regeln aus der TOML-Datei.

    Raises:
        PaperTradingRulesError: Wenn die Datei fehlt oder strukturell ungültig ist.
    """
    rules_path = path or PAPER_TRADING_RULES_FILE
    if not rules_path.is_file():
        raise PaperTradingRulesError(f"Paper-Trading-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise PaperTradingRulesError(
            f"Paper-Trading-Regeln sind kein gültiges TOML: {error}"
        ) from error
    return load_paper_trading_rules_from_dict(data)


def load_paper_trading_rules_from_dict(data: dict[str, Any]) -> PaperTradingRules:
    """Baut :class:`PaperTradingRules` aus einer bereits geparsten TOML-Struktur.

    Raises:
        PaperTradingRulesError: Wenn die Struktur ungültig ist.
    """
    models = {name: dict(cfg) for name, cfg in data.items() if name not in _RESERVED_SECTIONS}
    if not models:
        raise PaperTradingRulesError("Keine Paper-Trading-Modelle in der Regeldatei definiert.")

    runner_raw = data.get("runner", {})
    if not isinstance(runner_raw, dict):
        raise PaperTradingRulesError("Abschnitt [runner] muss eine Tabelle sein.")
    try:
        runner = PaperRunnerParams(
            warmup_bars=int(runner_raw.get("warmup_bars", 200)),
            step=int(runner_raw.get("step", 1)),
            max_holding_days=int(runner_raw.get("max_holding_days", 10)),
            trailing_distance=float(runner_raw.get("trailing_distance", 0.0)),
        )
    except (TypeError, ValueError) as error:
        raise PaperTradingRulesError(f"Ungültige Paper-Trading-Parameter: {error}") from error

    if runner.warmup_bars < 1 or runner.step < 1 or runner.max_holding_days < 1:
        raise PaperTradingRulesError("[runner]-Parameter müssen mindestens 1 sein.")
    if runner.trailing_distance < 0:
        raise PaperTradingRulesError("[runner].trailing_distance darf nicht negativ sein.")

    meta = data.get("meta", {})
    return PaperTradingRules(models=models, runner=runner, version=int(meta.get("version", 0)))


class PaperTradingEngine:
    """Bewertet die bestehenden Empfehlungen mit einem simulierten Portfolio.

    Args:
        runner: Der vollständige :class:`IntegrationRunner` (unveränderte Kette).
        settings: Projektkonfiguration (Kapital/Fractional/max. Positionen).
        rules: Geladene Paper-Trading-Regeln.
        registry: Registry der Paper-Trading-Modelle (Standard: alle Standardmodelle).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        runner: IntegrationRunner,
        settings: Settings,
        rules: PaperTradingRules,
        registry: PaperTradingRegistry | None = None,
        cache: PaperTradingCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._runner = runner
        self._settings = settings
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer
        self._paper_runner = PaperRunner(runner, rules.runner)

    @classmethod
    def from_config(
        cls,
        settings_path: Path | None = None,
        rules_path: Path | None = None,
        cache: PaperTradingCache | None = None,
    ) -> PaperTradingEngine:
        """Erzeugt eine Engine aus den Konfigurations-/Regeldateien."""
        return cls(
            runner=IntegrationRunner.from_config(),
            settings=load_settings(settings_path),
            rules=load_paper_trading_rules(rules_path),
            cache=cache,
        )

    def run(self, market_result: MarketResult, timeframe: str = "base") -> PaperTradingReport:
        """Simuliert alle Symbole eines MarketResult in **einem** Portfolio.

        Alle Symbole werden über dasselbe simulierte Portfolio geführt (ein
        gemeinsames Depot), sodass Kapital, Exposure und Drawdown portfolioweit
        gelten.
        """
        cache_key = self._cache_key(market_result, timeframe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._run(market_result, timeframe)
        report = replace(report, calculation_time=self._timer() - start)
        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def run_frame(
        self, frame: pd.DataFrame | None, symbol: str, timeframe: str = "base"
    ) -> PaperTradingReport:
        """Simuliert ein einzelnes Symbol als OHLCV-DataFrame."""
        problems = _validate_frame(frame)
        if problems:
            return self._empty_report(problems)
        assert frame is not None
        portfolio = self._new_portfolio()
        warnings = self._paper_runner.run(
            frame, symbol, portfolio, self._settings.risk.max_open_positions, timeframe
        )
        return self._build_report(portfolio, symbol, timeframe, warnings)

    def _run(self, market_result: MarketResult, timeframe: str) -> PaperTradingReport:
        """Führt die Simulation über alle Symbole eines gemeinsamen Portfolios aus."""
        symbols = market_result.symbols
        if not symbols:
            return self._empty_report(["Keine Symbole im MarketResult."])
        portfolio = self._new_portfolio()
        warnings: list[str] = []
        valid = True
        for symbol in symbols:
            frame = market_result.frame(symbol)
            problems = _validate_frame(frame)
            if problems:
                warnings.extend(f"[{symbol}] {p}" for p in problems)
                valid = False
                continue
            warnings.extend(
                self._paper_runner.run(
                    frame, symbol, portfolio, self._settings.risk.max_open_positions, timeframe
                )
            )
        label = symbols[0] if len(symbols) == 1 else ",".join(symbols)
        report = self._build_report(portfolio, label, timeframe, warnings)
        return replace(report, valid=report.valid and valid)

    def _new_portfolio(self) -> PaperPortfolio:
        """Erzeugt ein frisches Portfolio aus den Kontoeinstellungen."""
        return PaperPortfolio(
            starting_capital=self._settings.account.capital,
            fractional_shares=self._settings.account.fractional_shares,
        )

    def _build_report(
        self, portfolio: PaperPortfolio, symbol: str, timeframe: str, warnings: list[str]
    ) -> PaperTradingReport:
        """Baut den Report aus dem Portfolio und den Registry-Modellen."""
        positions = portfolio.positions()
        trades = trade_mod.build_trades(positions)
        context = PaperTradingContext(
            symbol=symbol,
            timeframe=timeframe,
            starting_capital=portfolio.starting_capital,
            current_equity=portfolio.equity(),
            positions=positions,
            trades=trades,
            equity_curve=portfolio.equity_curve,
            maximum_drawdown_pct=portfolio.maximum_drawdown_pct,
            running_drawdown_pct=portfolio.running_drawdown_pct(),
            exposure_pct=portfolio.exposure_pct(),
            realized_pnl=portfolio.realized_pnl,
            unrealized_pnl=portfolio.unrealized_pnl(),
        )
        outputs, model_warnings, model_ok = self._run_models(context)
        warnings = [*warnings, *model_warnings]

        statistics = self._statistics(outputs, context)
        performance = self._performance(outputs, context)
        results = [self._result_for(portfolio, position) for position in positions]

        return PaperTradingReport(
            results=results,
            statistics=statistics,
            performance=performance,
            journal=portfolio.journal.entries(),
            orders=portfolio.orders,
            valid=model_ok,
            warnings=warnings,
            metadata={
                "symbol": symbol,
                "timeframe": timeframe,
                "rules_version": self._rules.version,
                "position_count": len(positions),
                "model_metrics": {name: out.metrics for name, out in outputs.items()},
            },
        )

    def _run_models(
        self, context: PaperTradingContext
    ) -> tuple[dict[str, PaperTradingModelOutput], list[str], bool]:
        """Führt alle aktivierten, registrierten Paper-Trading-Modelle aus."""
        outputs: dict[str, PaperTradingModelOutput] = {}
        warnings: list[str] = []
        valid = True
        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Paper-Trading-Modell '{name}' ist nicht registriert.")
                continue
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                outputs[name] = self._registry.get(name).compute(context, params)
            except PaperTradingParameterError as error:
                valid = False
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Paper-Trading-Modell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
                continue
            warnings.extend(outputs[name].warnings)
        return outputs, warnings, valid

    @staticmethod
    def _statistics(
        outputs: dict[str, PaperTradingModelOutput], context: PaperTradingContext
    ) -> PaperStatistics:
        """Liest die Statistik aus dem Modell (mit neutralem Fallback)."""
        model = outputs.get("statistics_model")
        if model is not None and isinstance(model.details.get("statistics"), PaperStatistics):
            return model.details["statistics"]
        return PaperStatistics(
            current_equity=context.current_equity,
            open_positions=len(context.open_positions),
            closed_positions=len(context.closed_positions),
        )

    @staticmethod
    def _performance(
        outputs: dict[str, PaperTradingModelOutput], context: PaperTradingContext
    ) -> PaperPerformance:
        """Liest die Performance aus dem Modell (mit neutralem Fallback)."""
        model = outputs.get("performance_model")
        if model is not None and isinstance(model.details.get("performance"), PaperPerformance):
            return model.details["performance"]
        return PaperPerformance(
            starting_capital=context.starting_capital,
            current_equity=context.current_equity,
            equity_curve=list(context.equity_curve),
        )

    def _result_for(self, portfolio: PaperPortfolio, position: PaperPosition) -> PaperTradingResult:
        """Baut ein :class:`PaperTradingResult` aus Position und Portfolio-Kontext."""
        ctx = portfolio.context_for(position.position_id)
        return PaperTradingResult(
            paper_trading_id=f"paper:{position.position_id}",
            recommendation_id=position.recommendation_id,
            symbol=position.symbol,
            direction=position.direction,
            recommendation_strength=position.recommendation_strength,
            status=position.status,
            entry_price=position.entry_price,
            current_price=position.current_price,
            exit_price=position.exit_price,
            position_size=position.position_size,
            shares=position.shares,
            fractional_shares=self._settings.account.fractional_shares,
            entry_time=position.entry_time,
            exit_time=position.exit_time,
            pnl=position.pnl,
            pnl_pct=position.pnl_pct,
            running_drawdown=ctx["running_drawdown"],
            maximum_drawdown=ctx["maximum_drawdown"],
            current_equity=ctx["current_equity"],
            portfolio_exposure=ctx["portfolio_exposure"],
            close_reason=position.close_reason,
            reasons=list(position.reasons),
            warnings=list(position.warnings),
            metadata=dict(position.metadata),
            timestamp=datetime.now(UTC),
        )

    def _empty_report(self, problems: list[str]) -> PaperTradingReport:
        """Liefert einen leeren, aber konsistenten Report bei ungültigen Daten."""
        capital = self._settings.account.capital
        return PaperTradingReport(
            results=[],
            statistics=PaperStatistics(current_equity=capital),
            performance=PaperPerformance(starting_capital=capital, current_equity=capital),
            valid=False,
            warnings=problems,
            metadata={"rules_version": self._rules.version},
        )

    def _cache_key(self, market_result: MarketResult, timeframe: str) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        parts = []
        for sym in market_result.symbols:
            frame = market_result.frame(sym)
            parts.append(f"{sym}:{0 if frame is None else len(frame)}")
        return f"{timeframe}|{self._rules.version}|{'|'.join(parts)}"


def _validate_frame(frame: pd.DataFrame | None) -> list[str]:
    """Prüft die Eingabedaten (leere Historie, fehlende Spalten, Preise)."""
    if frame is None or frame.empty:
        return ["Leere Historie – kein Paper Trading möglich."]
    for col in (COL_HIGH, COL_LOW, COL_CLOSE):
        if col not in frame.columns:
            return [f"Spalte '{col}' fehlt – kein Paper Trading möglich."]
    closes = frame[COL_CLOSE].dropna()
    problems: list[str] = []
    if closes.empty:
        problems.append("Keine gültigen Schlusskurse in der Historie.")
    elif (closes <= 0).any():
        problems.append("Ungültige Preise (≤ 0) in der Historie.")
    if not frame.index.is_monotonic_increasing:
        problems.append("Ungültiger Zeitraum: Zeitindex ist nicht aufsteigend sortiert.")
    return problems


__all__ = [
    "PaperTradingEngine",
    "PaperTradingRules",
    "PaperTradingRulesError",
    "load_paper_trading_rules",
    "load_paper_trading_rules_from_dict",
]
