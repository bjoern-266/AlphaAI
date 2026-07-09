"""Gemeinsame Schnittstelle und Hilfsmittel für Risk-Modelle.

Alle Risk-Modelle implementieren :class:`BaseRiskModel` und geben ihr Ergebnis
als :class:`~models.risk.RiskModelOutput` zurück. Die reinen Datentypen liegen
in :mod:`models.risk`; :class:`RiskParameterError` in :mod:`core.exceptions`.
Beide werden hier zur Rückwärtskompatibilität re-exportiert.

Hier stehen außerdem die gemeinsamen **Hilfsmittel**: Parameterprüfung,
Gewichtsvalidierung, lineare Risiko-Skalierung, die **Positionsgrößen-Berechnung**
und die drei nicht-modellierten Basiskomponenten (ATR, Datenqualität, News).
Sie sind kein eigenes Modell, damit kein Modell von einem anderen abhängt.

Die Modelle bewerten Risiko ausschließlich objektiv – keine Kauf-/
Verkaufsentscheidung, keine Order, keine Positionseröffnung.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from core.exceptions import RiskParameterError
from models.risk import (
    RISK_COMPONENT_NAMES,
    OpenPosition,
    PositionSizing,
    RiskComponent,
    RiskContext,
    RiskLevel,
    RiskModelOutput,
)

__all__ = [
    "RiskParameterError",
    "RiskLevel",
    "RiskComponent",
    "RiskModelOutput",
    "RiskContext",
    "PositionSizing",
    "OpenPosition",
    "RISK_COMPONENT_NAMES",
    "BaseRiskModel",
    "require_float",
    "require_int",
    "require_bool",
    "validate_weights",
    "weighted_sum",
    "scaled_risk",
    "clamp_risk",
    "compute_position_sizing",
    "atr_component",
    "data_quality_component",
    "news_component",
]


class BaseRiskModel(ABC):
    """Basisklasse für alle Risk-Modelle.

    Attributes:
        name: Eindeutiger Modellname (= Schlüssel in ``risk_rules.toml``).
        component: Name der Risikokomponente, die dieses Modell füllt
            (aus :data:`RISK_COMPONENT_NAMES`), oder ``""`` (z. B.
            Positionsgröße trägt keine Komponente zum Gesamtrisiko bei).
        value_range: Beschreibung des Wertebereichs (Dokumentation).
    """

    name: str = "base"
    component: str = ""
    value_range: str = "0..100"

    @abstractmethod
    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Risiko dieses Modells.

        Args:
            context: Score, Indikatoren, Rohdaten, Konto-/Risikoparameter.
            params: Parameter des Modells (aus ``risk_rules.toml``).

        Returns:
            Ein :class:`RiskModelOutput` (Wert 0..100, höher = riskanter).
        """
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Parameter-Hilfen                                                             #
# --------------------------------------------------------------------------- #


def require_float(params: Mapping[str, Any], key: str, model: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (≥ 0)."""
    if key not in params:
        raise RiskParameterError(f"Risk-Modell '{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise RiskParameterError(
            f"Risk-Modell '{model}': Parameter '{key}' muss eine Zahl ≥ 0 sein."
        )
    return float(value)


def require_int(params: Mapping[str, Any], key: str, model: str) -> int:
    """Liest einen ganzzahligen Pflichtparameter (> 0)."""
    if key not in params:
        raise RiskParameterError(f"Risk-Modell '{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise RiskParameterError(
            f"Risk-Modell '{model}': Parameter '{key}' muss eine positive Ganzzahl sein."
        )
    return value


def require_bool(params: Mapping[str, Any], key: str, model: str) -> bool:
    """Liest einen booleschen Pflichtparameter."""
    if key not in params:
        raise RiskParameterError(f"Risk-Modell '{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if not isinstance(value, bool):
        raise RiskParameterError(
            f"Risk-Modell '{model}': Parameter '{key}' muss ein Wahrheitswert sein."
        )
    return value


def validate_weights(
    params: Mapping[str, Any], expected: Sequence[str], model: str, tolerance: float = 0.001
) -> dict[str, float]:
    """Prüft und normalisiert Gewichte (Summe 100 %, je 0..1).

    Raises:
        RiskParameterError: Bei fehlenden/unbekannten Komponenten, ungültigen
            Gewichten oder einer Gewichtssumme ungleich 100 %.
    """
    missing = [key for key in expected if key not in params]
    if missing:
        raise RiskParameterError(f"'{model}': fehlende Gewichte {missing}.")
    unknown = [key for key in params if key not in expected]
    if unknown:
        raise RiskParameterError(f"'{model}': unbekannte Gewichte {unknown}.")

    weights: dict[str, float] = {}
    for key in expected:
        value = params[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0.0 <= value <= 1.0
        ):
            raise RiskParameterError(
                f"'{model}': ungültiges Gewicht '{key}'={value} (erwartet 0..1)."
            )
        weights[key] = float(value)

    total = sum(weights.values())
    if abs(total - 1.0) > tolerance:
        raise RiskParameterError(f"'{model}': Gewichte summieren zu {total * 100:.1f} % (≠ 100 %).")
    return weights


def weighted_sum(weights: Mapping[str, float], components: Mapping[str, RiskComponent]) -> float:
    """Bildet die gewichtete Summe der Komponentenwerte (0..100)."""
    return float(sum(weight * components[name].value for name, weight in weights.items()))


# --------------------------------------------------------------------------- #
# Risiko-Skalierung                                                            #
# --------------------------------------------------------------------------- #


def clamp_risk(value: float) -> float:
    """Begrenzt einen Risikowert auf 0..100."""
    return float(min(100.0, max(0.0, value)))


def scaled_risk(value: float, low: float, high: float) -> float:
    """Skaliert einen Messwert linear auf ein Risiko 0..100.

    Werte ``≤ low`` ergeben 0 (geringes Risiko), Werte ``≥ high`` ergeben 100
    (hohes Risiko), dazwischen linear. Ist ``high ≤ low``, wird 0 geliefert.
    """
    if high <= low:
        return 0.0
    return clamp_risk((value - low) / (high - low) * 100.0)


# --------------------------------------------------------------------------- #
# Positionsgrößen-Berechnung (gemeinsames Hilfsmittel)                         #
# --------------------------------------------------------------------------- #


def compute_position_sizing(context: RiskContext, params: Mapping[str, Any]) -> PositionSizing:
    """Berechnet Positionsgröße, Order- und Kostenschätzung aus dem Risiko.

    Ausschließlich Konto-/Risikowerte aus ``settings.toml`` (über den Kontext)
    und Ausführungsparameter aus ``risk_rules.toml`` (über ``params``). Es wird
    **keine** Order erzeugt – nur eine nachvollziehbare Empfehlung.

    Raises:
        RiskParameterError: Bei ungültigen Parametern (z. B. RR ≤ 0).
    """
    atr_stop_multiplier = require_float(params, "atr_stop_multiplier", "position_sizing")
    risk_reward = require_float(params, "risk_reward", "position_sizing")
    slippage_bps = require_float(params, "slippage_bps", "position_sizing")
    commission_pct = require_float(params, "commission_pct", "position_sizing")
    min_commission = require_float(params, "min_commission", "position_sizing")
    max_position_pct = require_float(params, "max_position_pct", "position_sizing")
    max_portfolio_pct = require_float(params, "max_portfolio_exposure_pct", "position_sizing")
    if risk_reward <= 0:
        raise RiskParameterError("position_sizing: 'risk_reward' muss größer als 0 sein.")
    if atr_stop_multiplier <= 0:
        raise RiskParameterError("position_sizing: 'atr_stop_multiplier' muss größer als 0 sein.")

    capital = context.account.capital
    risk_pct = context.risk.risk_per_trade_pct
    max_positions = context.risk.max_open_positions
    max_portfolio_exposure = capital * max_portfolio_pct
    base = PositionSizing(
        maximum_risk_pct=risk_pct * 100.0,
        maximum_portfolio_exposure=max_portfolio_exposure,
        suggested_risk_reward=risk_reward,
    )

    price = context.entry_price
    atr = context.atr
    if capital <= 0 or price is None or price <= 0 or atr is None or atr <= 0:
        # Ohne gültigen Preis/ATR keine Stückzahl – nur die Rahmenwerte.
        return base

    risk_amount = capital * risk_pct
    stop_distance = atr * atr_stop_multiplier
    value_by_risk = (risk_amount / stop_distance) * price
    per_position_cap = capital * max_position_pct
    equal_weight_cap = capital / max_positions
    position_value = max(0.0, min(value_by_risk, per_position_cap, equal_weight_cap))

    shares = position_value / price
    if not context.account.fractional_shares:
        shares = float(math.floor(shares))
    order_value = shares * price
    slippage = order_value * slippage_bps / 10000.0
    commission = max(min_commission, order_value * commission_pct) if shares > 0 else 0.0

    return PositionSizing(
        suggested_position_size=position_value,
        maximum_risk_pct=risk_pct * 100.0,
        maximum_portfolio_exposure=max_portfolio_exposure,
        estimated_shares=shares,
        estimated_order_value=order_value,
        estimated_slippage=slippage,
        estimated_commission=commission,
        suggested_stop_distance=stop_distance,
        suggested_take_profit=stop_distance * risk_reward,
        suggested_risk_reward=risk_reward,
    )


# --------------------------------------------------------------------------- #
# Basiskomponenten (kein eigenes Modell)                                       #
# --------------------------------------------------------------------------- #


def atr_component(context: RiskContext, params: Mapping[str, Any]) -> RiskComponent:
    """ATR-Risiko aus dem ATR im Verhältnis zum Preis (ATR %)."""
    low = require_float(params, "atr_low_pct", "atr")
    high = require_float(params, "atr_high_pct", "atr")
    price = context.entry_price
    atr = context.atr
    if price is None or price <= 0 or atr is None or atr <= 0:
        return RiskComponent("atr", 50.0, "ATR: unvollständige Daten (neutral).")
    atr_pct = atr / price * 100.0
    value = scaled_risk(atr_pct, low, high)
    return RiskComponent("atr", value, f"ATR: {atr_pct:.2f} % des Preises.")


def data_quality_component(context: RiskContext) -> RiskComponent:
    """Datenqualitäts-Risiko: geringe Datenqualität ⇒ höheres Risiko."""
    quality = float(context.score_result.component_scores.get("data_quality", 100.0))
    value = clamp_risk(100.0 - quality)
    note = "vollständig" if value < 20.0 else "eingeschränkt"
    return RiskComponent("data_quality", value, f"Data Quality: {quality:.0f}/100 ({note}).")


def news_component(context: RiskContext, params: Mapping[str, Any]) -> RiskComponent:
    """News-Risiko – **vorbereitet**: neutraler Wert bis eine Quelle angebunden ist."""
    default = require_float(params, "news_default", "news")
    return RiskComponent(
        "news", clamp_risk(default), "News: vorbereitet, keine Quelle angebunden (neutral)."
    )
