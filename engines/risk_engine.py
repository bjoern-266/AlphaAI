"""Risk Engine – bewertet jede Hypothese objektiv nach Risiko.

Die :class:`RiskEngine` nimmt einen :class:`~engines.score_result.ScoreReport`
(plus Indikatoren und optionale Rohdaten) entgegen und liefert einen
:class:`~engines.risk_result.RiskReport`. Sie berechnet **ausschließlich
Risiko** und eine nachvollziehbare Positionsgrößen-Empfehlung – **keine**
Kauf-/Verkaufsentscheidung, **keine** Positionseröffnung, **keine** Order.

Jedes Risiko ist über seine zehn Komponenten vollständig erklärbar. Parameter
stammen ausschließlich aus ``knowledge/risk_rules.toml``; Konto-/Risikowerte
(Depotgröße, Fractional Shares, Risiko je Trade, max. Positionen) ausschließlich
aus ``config/settings.toml``. Neue Risk-Modelle werden nur über die
``RiskRegistry`` ergänzt – die Engine bleibt unverändert.

Portfolio-Vorbereitung: Die Engine reicht bereits eine Liste offener Positionen
(``open_positions``) an die Modelle durch, sodass Portfolio-/Korrelationsrisiko
voll implementiert werden kann, sobald offene Positionen geführt werden.
"""

from __future__ import annotations

import time
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings
from core.exceptions import AlphaAIError
from core.logging_config import get_logger
from core.paths import RISK_RULES_FILE
from engines.indicator_result import IndicatorResult
from engines.risk_cache import RiskCache
from engines.risk_registry import RiskRegistry, build_default_registry
from engines.risk_result import RiskReport, RiskResult
from engines.score_result import ScoreReport, ScoreResult
from models.risk import (
    RISK_COMPONENT_NAMES,
    OpenPosition,
    PositionSizing,
    RiskComponent,
    RiskContext,
    RiskLevel,
)
from risk.base import (
    RiskParameterError,
    atr_component,
    data_quality_component,
    news_component,
    validate_weights,
    weighted_sum,
)

_logger = get_logger(__name__)


class RiskRulesError(AlphaAIError):
    """Wird ausgelöst, wenn die Risk-Regeln fehlen oder ungültig sind."""


@dataclass(frozen=True, slots=True)
class RiskRules:
    """Geladene Risk-Regeln.

    Attributes:
        models: Zuordnung Modellname -> Parameter (inkl. ``enabled``).
        overall_weights: Gewichte der zehn Risikokomponenten (Summe 100 %).
        level_low_max: Obergrenze des Gesamtrisikos für Stufe LOW.
        level_medium_max: Obergrenze des Gesamtrisikos für Stufe MEDIUM.
        component_params: Parameter der Basiskomponenten (ATR, News).
        version: Versionsnummer der Regeldatei (Teil des Cache-Schlüssels).
    """

    models: dict[str, dict[str, Any]]
    overall_weights: dict[str, float]
    level_low_max: float
    level_medium_max: float
    component_params: dict[str, Any]
    version: int


_RESERVED_SECTIONS = frozenset({"meta", "overall", "levels", "components"})


def load_risk_rules(path: Path | None = None) -> RiskRules:
    """Lädt die Risk-Regeln aus der TOML-Datei.

    Raises:
        RiskRulesError: Wenn die Datei fehlt oder strukturell ungültig ist.
    """
    rules_path = path or RISK_RULES_FILE
    if not rules_path.is_file():
        raise RiskRulesError(f"Risk-Regeldatei nicht gefunden: {rules_path}")
    try:
        with rules_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise RiskRulesError(f"Risk-Regeln sind kein gültiges TOML: {error}") from error

    models = {name: dict(cfg) for name, cfg in data.items() if name not in _RESERVED_SECTIONS}
    if not models:
        raise RiskRulesError("Keine Risk-Modelle in der Regeldatei definiert.")

    overall = data.get("overall")
    if not isinstance(overall, dict):
        raise RiskRulesError("Abschnitt [overall] mit den Komponentengewichten fehlt.")
    try:
        weights = validate_weights(overall, RISK_COMPONENT_NAMES, "overall")
    except RiskParameterError as error:
        raise RiskRulesError(str(error)) from error

    levels = data.get("levels", {})
    low_max = float(levels.get("low_max", 33.0))
    medium_max = float(levels.get("medium_max", 66.0))
    if not 0 < low_max < medium_max < 100:
        raise RiskRulesError("[levels]: 0 < low_max < medium_max < 100 muss gelten.")

    meta = data.get("meta", {})
    return RiskRules(
        models=models,
        overall_weights=weights,
        level_low_max=low_max,
        level_medium_max=medium_max,
        component_params=dict(data.get("components", {})),
        version=int(meta.get("version", 0)),
    )


class RiskEngine:
    """Bewertet Hypothesen objektiv nach Risiko anhand konfigurierter Modelle.

    Args:
        rules: Geladene Risk-Regeln (Gewichte, Schwellen, Modellparameter).
        settings: Projektkonfiguration (liefert Konto- und Risikowerte).
        registry: Registry der Risk-Modelle (Standard: alle Standardmodelle).
        cache: Optionaler Cache für Ergebnisse.
        timer: Zeitquelle zur Messung der Rechenzeit (injizierbar für Tests).
    """

    def __init__(
        self,
        rules: RiskRules,
        settings: Settings,
        registry: RiskRegistry | None = None,
        cache: RiskCache | None = None,
        timer: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._rules = rules
        self._settings = settings
        self._registry = registry or build_default_registry()
        self._cache = cache
        self._timer = timer

    @classmethod
    def from_config(
        cls,
        rules_path: Path | None = None,
        settings_path: Path | None = None,
        cache: RiskCache | None = None,
    ) -> RiskEngine:
        """Erzeugt eine Engine mit Regeln und Einstellungen aus den Dateien."""
        return cls(
            rules=load_risk_rules(rules_path),
            settings=load_settings(settings_path),
            cache=cache,
        )

    def assess(
        self,
        score_report: ScoreReport,
        indicators: IndicatorResult,
        data: pd.DataFrame | None = None,
        symbol: str = "",
        timeframe: str = "base",
        open_positions: Sequence[OpenPosition] = (),
    ) -> RiskReport:
        """Bewertet das Risiko aller Scores des Score-Reports."""
        cache_key = self._cache_key(
            score_report, indicators, symbol, timeframe, len(open_positions)
        )
        if self._cache is not None:
            cached = self._cache.get(cache_key)
            if cached is not None:
                return cached

        start = self._timer()
        report = self._assess(score_report, indicators, data, symbol, timeframe, open_positions)
        # Report ist unveränderlich (frozen): Rechenzeit über eine Kopie setzen.
        report = replace(report, calculation_time=self._timer() - start)

        if self._cache is not None:
            self._cache.set(cache_key, report)
        return report

    def _assess(
        self,
        score_report: ScoreReport,
        indicators: IndicatorResult,
        data: pd.DataFrame | None,
        symbol: str,
        timeframe: str,
        open_positions: Sequence[OpenPosition],
    ) -> RiskReport:
        """Kern der Bewertung inkl. Validierung (ohne Zeitmessung/Cache).

        Sammelt Bewertungen/Warnungen/Gültigkeit lokal und konstruiert den
        unveränderlichen :class:`RiskReport` **einmalig** am Ende.
        """
        capital = self._settings.account.capital
        metadata: dict[str, Any] = {
            "symbol": symbol,
            "timeframe": timeframe,
            "rules_version": self._rules.version,
            "capital": capital,
            "open_positions": len(open_positions),
        }
        warnings: list[str] = []
        results: list[RiskResult] = []
        valid = True

        if capital <= 0:
            warnings.append("Negative/ungültige Depotgröße – keine Risikobewertung möglich.")
            return RiskReport(valid=False, warnings=warnings, metadata=metadata)
        if not score_report.valid:
            valid = False
            warnings.append("Ungültiger/fehlender Score-Report.")
        if not score_report.results:
            warnings.append("Keine Scores zum Bewerten vorhanden.")
            return RiskReport(results=results, valid=valid, warnings=warnings, metadata=metadata)

        for score_result in score_report.results:
            risk_result, model_ok = self._assess_one(
                score_result, indicators, data, symbol, timeframe, open_positions
            )
            results.append(risk_result)
            if not model_ok:
                valid = False

        metadata["assessed"] = len(results)
        return RiskReport(results=results, valid=valid, warnings=warnings, metadata=metadata)

    def _assess_one(
        self,
        score_result: ScoreResult,
        indicators: IndicatorResult,
        data: pd.DataFrame | None,
        symbol: str,
        timeframe: str,
        open_positions: Sequence[OpenPosition],
    ) -> tuple[RiskResult, bool]:
        """Bewertet das Risiko einer einzelnen Hypothese über alle Modelle."""
        context = RiskContext(
            score_result=score_result,
            indicators=indicators,
            account=self._settings.account,
            risk=self._settings.risk,
            data=data,
            open_positions=tuple(open_positions),
            symbol=symbol,
            timeframe=timeframe,
        )

        components: dict[str, RiskComponent] = {}
        model_values: dict[str, float] = {}
        sizing = PositionSizing(
            maximum_risk_pct=self._settings.risk.risk_per_trade_pct * 100.0,
            maximum_portfolio_exposure=context.account.capital,
        )
        reasons: list[str] = []
        warnings: list[str] = []
        valid = True

        for name, cfg in self._rules.models.items():
            if not cfg.get("enabled", False):
                continue
            if name not in self._registry:
                warnings.append(f"Risk-Modell '{name}' ist nicht registriert.")
                continue
            model = self._registry.get(name)
            params = {key: value for key, value in cfg.items() if key != "enabled"}
            try:
                output = model.compute(context, params)
            except RiskParameterError as error:
                valid = False
                warnings.append(str(error))
                continue
            except Exception as error:  # Fehler eines Modells isoliert behandeln.
                _logger.warning("Risk-Modell '%s' fehlgeschlagen: %s", name, error)
                warnings.append(f"Berechnung von '{name}' fehlgeschlagen: {error}")
                continue

            model_values[name] = output.value
            warnings.extend(output.warnings)
            reasons.extend(f"[{name}] {reason}" for reason in output.reasons)
            if model.component:
                first_reason = output.reasons[0] if output.reasons else ""
                components[model.component] = RiskComponent(
                    model.component, output.value, first_reason
                )
            if name == "position_sizing" and isinstance(
                output.details.get("sizing"), PositionSizing
            ):
                sizing = output.details["sizing"]

        # Basiskomponenten (kein eigenes Modell): ATR, Datenqualität, News.
        try:
            components["atr"] = atr_component(context, self._rules.component_params)
            components["news"] = news_component(context, self._rules.component_params)
        except RiskParameterError as error:
            valid = False
            warnings.append(str(error))
        components["data_quality"] = data_quality_component(context)

        # Fehlende Komponenten neutral auffüllen (z. B. deaktiviertes Modell).
        for name in RISK_COMPONENT_NAMES:
            components.setdefault(
                name, RiskComponent(name, 50.0, f"{name}: nicht berechnet (neutral).")
            )

        # Eingabevalidierung (Preis/ATR) – ohne sie ist keine Stückzahl möglich.
        if context.entry_price is None:
            valid = False
            warnings.append("Ungültiger/fehlender Preis – keine Positionsgröße berechenbar.")
        if context.atr is None or context.atr <= 0:
            valid = False
            warnings.append("Ungültiger/fehlender ATR – keine Positionsgröße berechenbar.")

        overall = weighted_sum(self._rules.overall_weights, components)
        reasons.extend(self._transparency_lines(components))
        level = self._level(overall)

        result = RiskResult(
            risk_id=f"risk:{score_result.score_id}",
            score_id=score_result.score_id,
            hypothesis_id=score_result.hypothesis_id,
            overall_risk=float(min(100.0, max(0.0, overall))),
            risk_level=level,
            suggested_position_size=sizing.suggested_position_size,
            maximum_risk_pct=sizing.maximum_risk_pct,
            maximum_portfolio_exposure=sizing.maximum_portfolio_exposure,
            estimated_shares=sizing.estimated_shares,
            estimated_order_value=sizing.estimated_order_value,
            estimated_slippage=sizing.estimated_slippage,
            estimated_commission=sizing.estimated_commission,
            suggested_stop_distance=sizing.suggested_stop_distance,
            suggested_take_profit=sizing.suggested_take_profit,
            suggested_risk_reward=sizing.suggested_risk_reward,
            risk_components={name: comp.value for name, comp in components.items()},
            reasons=reasons,
            warnings=warnings,
            metadata={
                "model_values": model_values,
                "component_reasons": {name: comp.reason for name, comp in components.items()},
                "level_thresholds": {
                    "low_max": self._rules.level_low_max,
                    "medium_max": self._rules.level_medium_max,
                },
            },
            timestamp=score_result.timestamp,
        )
        return result, valid

    def _transparency_lines(self, components: dict[str, RiskComponent]) -> list[str]:
        """Erzeugt erklärbare Beitragszeilen je Komponente (z. B. ``volatility: 18/25``)."""
        weights = self._rules.overall_weights
        return [
            f"{name}: {weights[name] * components[name].value:.0f}/{weights[name] * 100:.0f}"
            for name in RISK_COMPONENT_NAMES
        ]

    def _level(self, overall: float) -> RiskLevel:
        """Bildet das Gesamtrisiko auf eine grobe Stufe ab."""
        if overall <= self._rules.level_low_max:
            return RiskLevel.LOW
        if overall <= self._rules.level_medium_max:
            return RiskLevel.MEDIUM
        return RiskLevel.HIGH

    def _cache_key(
        self,
        score_report: ScoreReport,
        indicators: IndicatorResult,
        symbol: str,
        timeframe: str,
        open_positions: int,
    ) -> str:
        """Bildet einen stabilen Cache-Schlüssel aus den Eingabe-Fingerabdrücken."""
        ind_fp = indicators.metadata.get("candle_count")
        return (
            f"{symbol}|{timeframe}|{score_report.score_count}|{ind_fp}|"
            f"{open_positions}|{self._rules.version}"
        )
