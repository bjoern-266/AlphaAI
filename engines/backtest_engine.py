"""Backtest Engine – bewertet bestehende Empfehlungen an historischen Daten.

Die :class:`BacktestEngine` verbindet den Historical Runner (führt die
**bestehende** Pipeline über die Historie aus) mit dem Trade-Simulator und den
Backtest-Modellen zu einem :class:`~models.backtest.BacktestReport`. Sie erzeugt
**keine** neue Handelsregel, verändert **keine** Empfehlung, führt **keine**
echte Order aus und simuliert Trades ausschließlich rechnerisch. Konto- und
Risikoeinstellungen stammen ausschließlich aus ``config/settings.toml`` (über die
bestehende Risk Engine).

Parameter des Backtests stammen ausschließlich aus
``knowledge/backtest_rules.toml``. Neue Backtest-Modelle werden nur über die
``BacktestRegistry`` ergänzt – die Engine bleibt unverändert.
"""

from __future__ import annotations

import math
import time
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backtesting.base import BacktestParameterError
from backtesting.benchmark import buy_and_hold
from backtesting.equity_curve import build_equity_curve
from backtesting.historical_runner import HistoricalRunner, HistoricalRunnerParams
from backtesting.trade_simulator import SimulationParams, TradeSimulator
from core.config import Settings, load_settings
from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import BACKTEST_RULES_FILE
from engines.backtest_cache import BacktestCache
from engines.backtest_registry import BacktestRegistry, build_default_registry
from models.backtest import (
    BacktestContext,
    BacktestModelOutput,
    BacktestReport,
    BacktestResult,
    BenchmarkResult,
    EquityPoint,
    HistoricalSignal,
    SimulatedTrade,
)
from models.market import COL_CLOSE, MarketResult
from pipeline.runner import IntegrationRunner

_logger = get_logger(__name__)

_RESERVED_SECTIONS = frozenset({"meta", "engine", "simulation"})


class BacktestRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Backtest-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class BacktestRules:
    """Geladene Backtest-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter (inkl. ``enabled``).
        runner: Parameter des Historical Runners.
        simulation: Parameter der Trade-Simulation.
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    runner: HistoricalRunnerParams
    simulation: SimulationParams
    version: int


def load_backtest_rules(path: Path | None = None) -> BacktestRules:
    """Lädt die Backtest-Regeln aus der TOML-Datei.

    Raises:
        BacktestRulesError: Wenn die Datei fehlt oder strukturell ungültig ist.
    """
    rules_path = path or BACKTEST_RULES_FILE
    if not rules_path.is_file():
        raise BacktestRulesError(f"Backtest-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise BacktestRulesError(f"Backtest-Regeln sind kein gültiges TOML: {error}") from error

    return load_backtest_rules_from_dict(data)


def load_backtest_rules_from_dict(data: dict[str, Any]) -> BacktestRules:
    """Baut :class:`BacktestRules` aus einer bereits geparsten TOML-Struktur.

    Raises:
        BacktestRulesError: Wenn die Struktur ungültig ist.
    """
    models = {name: dict(cfg) for name, cfg in data.items() if name not in _RESERVED_SECTIONS}
    if not models:
        raise BacktestRulesError("Keine Backtest-Modelle in der Regeldatei definiert.")

    engine_raw = data.get("engine", {})
    simulation_raw = data.get("simulation", {})
    if not isinstance(engine_raw, dict) or not isinstance(simulation_raw, dict):
        raise BacktestRulesError("Abschnitte [engine] und [simulation] müssen Tabellen sein.")

    try:
        runner = HistoricalRunnerParams(
            warmup_bars=int(engine_raw.get("warmup_bars", 200)),
            step=int(engine_raw.get("step", 5)),
            min_history_bars=int(engine_raw.get("min_history_bars", 210)),
        )
        simulation = SimulationParams(
            max_holding_bars=int(simulation_raw.get("max_holding_bars", 20)),
            apply_costs=bool(simulation_raw.get("apply_costs", True)),
            breakeven_epsilon=float(simulation_raw.get("breakeven_epsilon", 0.0)),
        )
    except (TypeError, ValueError) as error:
        raise BacktestRulesError(f"Ungültige Backtest-Parameter: {error}") from error

    if runner.warmup_bars < 1 or runner.step < 1 or runner.min_history_bars < 1:
        raise BacktestRulesError("[engine]-Parameter müssen mindestens 1 sein.")
    if simulation.max_holding_bars < 1:
        raise BacktestRulesError("[simulation].max_holding_bars muss mindestens 1 sein.")
    if simulation.breakeven_epsilon < 0:
        raise BacktestRulesError("[simulation].breakeven_epsilon darf nicht negativ sein.")

    meta = data.get("meta", {})
    return BacktestRules(
        models=models, runner=runner, simulation=simulation, version=int(meta.get("version", 0))
    )


class BacktestEngine:
    """Führt Backtests der bestehenden Empfehlungen auf historischen Daten aus.

    Args:
        runner: Der vollständige :class:`IntegrationRunner` (unveränderte Kette).
        settings: Projektkonfiguration (Startkapital aus ``settings.toml``).
        rules: Geladene Backtest-Regeln.
        registry: Registry der Backtest-Modelle (Standard: alle Standardmodelle).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        runner: IntegrationRunner,
        settings: Settings,
        rules: BacktestRules,
        registry: BacktestRegistry | None = None,
        cache: BacktestCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._runner = runner
        self._settings = settings
        self._rules = rules
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer
        self._historical = HistoricalRunner(runner, rules.runner)
        self._simulator = TradeSimulator(rules.simulation)

    @classmethod
    def from_config(
        cls,
        settings_path: Path | None = None,
        rules_path: Path | None = None,
        cache: BacktestCache | None = None,
    ) -> BacktestEngine:
        """Erzeugt eine Engine aus den Konfigurations-/Regeldateien."""
        return cls(
            runner=IntegrationRunner.from_config(),
            settings=load_settings(settings_path),
            rules=load_backtest_rules(rules_path),
            cache=cache,
        )

    def run(self, market_result: MarketResult, timeframe: str = "base") -> BacktestReport:
        """Backtestet alle Symbole eines MarketResult zu einem Report."""
        cache_key = self._cache_key(market_result, timeframe)
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        results: list[BacktestResult] = []
        warnings: list[str] = []
        valid = True
        for symbol in market_result.symbols:
            frame = market_result.frame(symbol)
            result = self.run_frame(frame, symbol, timeframe)
            results.append(result)
            if not result.valid:
                valid = False
        if not market_result.symbols:
            warnings.append("Keine Symbole im MarketResult.")
            valid = False

        report = BacktestReport(
            results=results,
            valid=valid,
            warnings=warnings,
            metadata={"rules_version": self._rules.version, "symbols": market_result.symbols},
        )
        report = replace(report, calculation_time=self._timer() - start)
        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def run_frame(
        self, frame: pd.DataFrame | None, symbol: str, timeframe: str = "base"
    ) -> BacktestResult:
        """Backtestet einen einzelnen historischen OHLCV-DataFrame.

        Validiert den Zeitraum/die Daten, führt die bestehende Pipeline über die
        Historie aus, simuliert die Trades und berechnet die Kennzahlen über die
        registrierten Modelle.
        """
        warnings: list[str] = []
        problems = self._validate_frame(frame)
        if problems:
            return self._empty_result(symbol, timeframe, problems)

        assert frame is not None  # durch _validate_frame sichergestellt
        signals, run_warnings = self._historical.generate(frame, symbol, timeframe)
        warnings.extend(run_warnings)
        trades, sim_warnings = self._simulator.simulate(signals, frame, symbol)
        warnings.extend(sim_warnings)

        capital = self._settings.account.capital
        start_time, end_time = _period(frame)
        equity_curve = build_equity_curve(trades, capital, start_time)
        benchmark = buy_and_hold(frame, capital)
        signal_count = sum(1 for s in signals if s.is_actionable)

        context = BacktestContext(
            symbol=symbol,
            timeframe=timeframe,
            starting_capital=capital,
            trades=trades,
            equity_curve=equity_curve,
            signal_count=signal_count,
            start_date=start_time,
            end_date=end_time,
            benchmark=benchmark,
            metadata={"bar_count": len(frame)},
        )
        outputs, model_warnings, model_ok = self._run_models(context)
        warnings.extend(model_warnings)

        return self._assemble_result(
            context, signals, trades, equity_curve, benchmark, outputs, warnings, model_ok
        )

    def _run_models(
        self, context: BacktestContext
    ) -> tuple[dict[str, BacktestModelOutput], list[str], bool]:
        """Führt alle aktivierten, registrierten Backtest-Modelle aus."""
        outputs: dict[str, BacktestModelOutput] = {}
        warnings: list[str] = []
        valid = True
        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Backtest-Modell '{name}' ist nicht registriert.")
                continue
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                outputs[name] = self._registry.get(name).compute(context, params)
            except BacktestParameterError as error:
                valid = False
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Backtest-Modell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
                continue
            warnings.extend(outputs[name].warnings)
        return outputs, warnings, valid

    def _assemble_result(
        self,
        context: BacktestContext,
        signals: list[HistoricalSignal],
        trades: list[SimulatedTrade],
        equity_curve: list[EquityPoint],
        benchmark: BenchmarkResult | None,
        outputs: dict[str, BacktestModelOutput],
        warnings: list[str],
        model_ok: bool,
    ) -> BacktestResult:
        """Baut das BacktestResult aus den Modell-Kennzahlen zusammen."""
        perf = outputs.get("performance_model")
        draw = outputs.get("drawdown_model")
        ratio = outputs.get("ratio_model")
        perf_metrics = perf.metrics if perf else {}
        draw_metrics = draw.metrics if draw else {}
        ratio_details = ratio.details if ratio else {}

        final_equity = draw_metrics.get("final_equity", context.starting_capital)
        total_return = draw_metrics.get("total_return", 0.0)
        total_return_pct = draw_metrics.get("total_return_pct", 0.0)
        reasons = [r for out in outputs.values() for r in out.reasons]
        valid, metric_warnings = self._validate_metrics(perf_metrics, draw_metrics, trades)
        warnings.extend(metric_warnings)
        valid = valid and model_ok

        summary = self._build_summary(
            context, len(trades), total_return_pct, draw_metrics, benchmark
        )
        return BacktestResult(
            backtest_id=f"bt:{context.symbol}:{context.timeframe}",
            symbol=context.symbol,
            timeframe=context.timeframe,
            start_date=context.start_date,
            end_date=context.end_date,
            signal_count=context.signal_count,
            trade_count=len(trades),
            win_rate=perf_metrics.get("win_rate", 0.0),
            loss_rate=perf_metrics.get("loss_rate", 0.0),
            profit_factor=perf_metrics.get("profit_factor", 0.0),
            average_win=perf_metrics.get("average_win", 0.0),
            average_loss=perf_metrics.get("average_loss", 0.0),
            average_risk_reward=perf_metrics.get("average_risk_reward", 0.0),
            average_holding_time=perf_metrics.get("average_holding_time", 0.0),
            maximum_drawdown=draw_metrics.get("maximum_drawdown", 0.0),
            expectancy=perf_metrics.get("expectancy", 0.0),
            sharpe_ratio=ratio_details.get("sharpe"),
            sortino_ratio=ratio_details.get("sortino"),
            calmar_ratio=ratio_details.get("calmar"),
            total_return=total_return,
            total_return_pct=total_return_pct,
            final_equity=final_equity,
            equity_curve=equity_curve,
            trades=trades,
            benchmark=benchmark,
            valid=valid,
            summary=summary,
            reasons=reasons,
            warnings=warnings,
            metadata={
                "signals": len(signals),
                "actionable_signals": context.signal_count,
                "rules_version": self._rules.version,
                "expectancy_r": perf_metrics.get("expectancy_r", 0.0),
                "model_metrics": {name: out.metrics for name, out in outputs.items()},
            },
            timestamp=datetime.now(UTC),
        )

    @staticmethod
    def _validate_metrics(
        perf_metrics: dict[str, float],
        draw_metrics: dict[str, float],
        trades: list[SimulatedTrade],
    ) -> tuple[bool, list[str]]:
        """Prüft die Kennzahlen auf Plausibilität (Ungültige Kennzahlen)."""
        warnings: list[str] = []
        valid = True
        for name, value in (*perf_metrics.items(), *draw_metrics.items()):
            if name == "profit_factor":
                continue  # ``inf`` (keine Verluste) ist ein zulässiger Sonderfall.
            if isinstance(value, float) and not math.isfinite(value):
                warnings.append(f"Kennzahl '{name}' ist nicht endlich ({value}).")
                valid = False
        win_rate = perf_metrics.get("win_rate")
        if win_rate is not None and not 0.0 <= win_rate <= 1.0:
            warnings.append(f"Win Rate {win_rate} außerhalb 0..1.")
            valid = False
        max_dd = draw_metrics.get("maximum_drawdown")
        if max_dd is not None and not 0.0 <= max_dd <= 100.0:
            warnings.append(f"Max Drawdown {max_dd} außerhalb 0..100 %.")
            valid = False
        return valid, warnings

    @staticmethod
    def _build_summary(
        context: BacktestContext,
        trade_count: int,
        total_return_pct: float,
        draw_metrics: dict[str, float],
        benchmark: BenchmarkResult | None,
    ) -> str:
        """Baut eine menschenlesbare Kurzfassung des Backtests."""
        max_dd = draw_metrics.get("maximum_drawdown", 0.0)
        body = (
            f"{context.symbol}: {trade_count} Trades aus {context.signal_count} Signalen, "
            f"Rendite {total_return_pct:+.2f} %, max. Drawdown {max_dd:.2f} %."
        )
        if benchmark is not None:
            alpha = total_return_pct - benchmark.return_pct
            body += (
                f" Benchmark ({benchmark.name}) {benchmark.return_pct:+.2f} % "
                f"⇒ Alpha {alpha:+.2f} %."
            )
        return body

    def _validate_frame(self, frame: pd.DataFrame | None) -> list[str]:
        """Prüft Zeitraum/Daten/Preise (leere Historie, ungültige Preise)."""
        problems: list[str] = []
        if frame is None or frame.empty:
            return ["Leere Historie – kein Backtest möglich."]
        if COL_CLOSE not in frame.columns:
            return ["Spalte 'close' fehlt – kein Backtest möglich."]
        closes = frame[COL_CLOSE].dropna()
        if closes.empty:
            problems.append("Keine gültigen Schlusskurse in der Historie.")
        elif (closes <= 0).any():
            problems.append("Ungültige Preise (≤ 0) in der Historie.")
        if len(frame) < self._rules.runner.min_history_bars:
            problems.append(
                f"Zu kurze Historie: {len(frame)} < {self._rules.runner.min_history_bars} Kerzen."
            )
        if not frame.index.is_monotonic_increasing:
            problems.append("Ungültiger Zeitraum: Zeitindex ist nicht aufsteigend sortiert.")
        return problems

    def _empty_result(self, symbol: str, timeframe: str, problems: list[str]) -> BacktestResult:
        """Liefert ein leeres, aber konsistentes Ergebnis bei ungültigen Daten."""
        return BacktestResult(
            backtest_id=f"bt:{symbol}:{timeframe}",
            symbol=symbol,
            timeframe=timeframe,
            start_date=None,
            end_date=None,
            signal_count=0,
            trade_count=0,
            win_rate=0.0,
            loss_rate=0.0,
            profit_factor=0.0,
            average_win=0.0,
            average_loss=0.0,
            average_risk_reward=0.0,
            average_holding_time=0.0,
            maximum_drawdown=0.0,
            expectancy=0.0,
            sharpe_ratio=None,
            sortino_ratio=None,
            calmar_ratio=None,
            total_return=0.0,
            total_return_pct=0.0,
            final_equity=self._settings.account.capital,
            equity_curve=[EquityPoint(None, self._settings.account.capital, 0.0, 0.0)],
            trades=[],
            benchmark=None,
            valid=False,
            summary=f"{symbol}: kein Backtest – {problems[0]}",
            reasons=[],
            warnings=problems,
            metadata={"rules_version": self._rules.version},
            timestamp=datetime.now(UTC),
        )

    def _cache_key(self, market_result: MarketResult, timeframe: str) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        parts = []
        for sym in market_result.symbols:
            frame = market_result.frame(sym)
            parts.append(f"{sym}:{0 if frame is None else len(frame)}")
        return f"{timeframe}|{self._rules.version}|{'|'.join(parts)}"


def _period(frame: pd.DataFrame) -> tuple[datetime | None, datetime | None]:
    """Ermittelt Anfangs- und Endzeitpunkt aus dem Zeitindex (falls vorhanden)."""
    if frame.empty:
        return None, None
    first = frame.index[0]
    last = frame.index[-1]
    return _as_datetime(first), _as_datetime(last)


def _as_datetime(value: object) -> datetime | None:
    """Wandelt einen Index-Eintrag – falls möglich – in ein ``datetime`` um."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return None


# MarketStatus wird für synthetische Eingaben in Tests/Aufrufern benötigt.
__all__ = [
    "BacktestEngine",
    "BacktestRules",
    "BacktestRulesError",
    "load_backtest_rules",
    "load_backtest_rules_from_dict",
]
