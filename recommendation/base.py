"""Gemeinsame Schnittstelle und Hilfsmittel für Recommendation-Modelle.

Alle Modelle implementieren :class:`BaseRecommendationModel` und geben ihr
Ergebnis als :class:`~models.recommendation.RecommendationModelOutput` zurück.
Die reinen Datentypen liegen in :mod:`models.recommendation`;
:class:`RecommendationParameterError` in :mod:`core.exceptions`. Beide werden
hier zur Rückwärtskompatibilität re-exportiert.

Hier stehen die gemeinsamen **Hilfsmittel**: die sechs Entscheidungsfaktoren,
das gewichtete Gesamtrating, die Confidence, die Stufen-/Handlungs-Zuordnung und
die **No-Trade-Gates**. Sie sind kein eigenes Modell, damit kein Modell von
einem anderen abhängt.

Grundsatz (No-Trade-Philosophie): „Kein Trade ist besser als ein schlechter
Trade." Ein hoher Score allein führt **nie** automatisch zu BUY/STRONG_BUY.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from typing import Any

from core.exceptions import RecommendationParameterError
from models.recommendation import (
    RECOMMENDATION_FACTOR_NAMES,
    RecommendationContext,
    RecommendationFactor,
    RecommendationLevel,
    RecommendationModelOutput,
    SuggestedAction,
)
from models.risk import RiskResult
from models.score import ScoreResult
from models.strategy import StrategyDirection, StrategyResult

__all__ = [
    "RecommendationParameterError",
    "RecommendationLevel",
    "SuggestedAction",
    "RecommendationFactor",
    "RecommendationModelOutput",
    "RecommendationContext",
    "RECOMMENDATION_FACTOR_NAMES",
    "BaseRecommendationModel",
    "require_float",
    "validate_weights",
    "weighted_sum",
    "clamp_rating",
    "clamp_confidence",
    "consensus_fraction",
    "compute_factors",
    "compute_overall_rating",
    "compute_confidence",
    "level_from_rating",
    "action_for_level",
    "cap_level",
    "level_severity",
    "is_neutral",
    "CONFIDENCE_WEIGHT_KEYS",
]

# Erwartete Schlüssel der Confidence-Gewichte (Reihenfolge = Dokumentation).
CONFIDENCE_WEIGHT_KEYS: tuple[str, ...] = (
    "strategy_confidence",
    "consensus",
    "risk",
    "data_quality",
)

# Schwere-Ordnung der Empfehlungsstufen (für Deckelung durch Gates).
_LEVEL_ORDER: tuple[RecommendationLevel, ...] = (
    RecommendationLevel.AVOID,
    RecommendationLevel.WAIT,
    RecommendationLevel.WATCH,
    RecommendationLevel.BUY,
    RecommendationLevel.STRONG_BUY,
)

_LEVEL_ACTION: dict[RecommendationLevel, SuggestedAction] = {
    RecommendationLevel.STRONG_BUY: SuggestedAction.OPEN,
    RecommendationLevel.BUY: SuggestedAction.OPEN,
    RecommendationLevel.WATCH: SuggestedAction.MONITOR,
    RecommendationLevel.WAIT: SuggestedAction.WAIT,
    RecommendationLevel.AVOID: SuggestedAction.SKIP,
}


class BaseRecommendationModel(ABC):
    """Basisklasse für alle Recommendation-Modelle.

    Attributes:
        name: Eindeutiger Modellname (= Schlüssel in
            ``recommendation_rules.toml``).
        value_range: Beschreibung des Wertebereichs (Dokumentation).
    """

    name: str = "base"
    value_range: str = "0..100"

    @abstractmethod
    def compute(
        self, context: RecommendationContext, params: Mapping[str, Any]
    ) -> RecommendationModelOutput:
        """Erzeugt den Beitrag dieses Modells zur Empfehlung.

        Args:
            context: Hypothese, Score, Risiko, Faktoren, Rating, Confidence.
            params: Parameter des Modells (aus ``recommendation_rules.toml``).

        Returns:
            Ein :class:`RecommendationModelOutput`.
        """
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Parameter-/Gewichts-Hilfen                                                   #
# --------------------------------------------------------------------------- #


def require_float(params: Mapping[str, Any], key: str, model: str) -> float:
    """Liest einen Gleitkomma-Pflichtparameter (≥ 0)."""
    if key not in params:
        raise RecommendationParameterError(f"'{model}': Parameter '{key}' fehlt.")
    value = params[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise RecommendationParameterError(f"'{model}': Parameter '{key}' muss eine Zahl ≥ 0 sein.")
    return float(value)


def validate_weights(
    params: Mapping[str, Any], expected: Sequence[str], model: str, tolerance: float = 0.001
) -> dict[str, float]:
    """Prüft und normalisiert Gewichte (Summe 100 %, je 0..1).

    Raises:
        RecommendationParameterError: Bei fehlenden/unbekannten Komponenten,
            ungültigen Gewichten oder einer Gewichtssumme ungleich 100 %.
    """
    missing = [key for key in expected if key not in params]
    if missing:
        raise RecommendationParameterError(f"'{model}': fehlende Gewichte {missing}.")
    unknown = [key for key in params if key not in expected]
    if unknown:
        raise RecommendationParameterError(f"'{model}': unbekannte Gewichte {unknown}.")

    weights: dict[str, float] = {}
    for key in expected:
        value = params[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0.0 <= value <= 1.0
        ):
            raise RecommendationParameterError(
                f"'{model}': ungültiges Gewicht '{key}'={value} (erwartet 0..1)."
            )
        weights[key] = float(value)

    total = sum(weights.values())
    if abs(total - 1.0) > tolerance:
        raise RecommendationParameterError(
            f"'{model}': Gewichte summieren zu {total * 100:.1f} % (≠ 100 %)."
        )
    return weights


def weighted_sum(weights: Mapping[str, float], values: Mapping[str, float]) -> float:
    """Bildet die gewichtete Summe (Werte 0..100)."""
    return float(sum(weight * values[name] for name, weight in weights.items()))


def clamp_rating(value: float) -> float:
    """Begrenzt ein Rating auf 0..100."""
    return float(min(100.0, max(0.0, value)))


def clamp_confidence(value: float) -> float:
    """Begrenzt eine Confidence auf 0..1."""
    return float(min(1.0, max(0.0, value)))


# --------------------------------------------------------------------------- #
# Faktoren, Rating, Confidence                                                 #
# --------------------------------------------------------------------------- #


def consensus_fraction(target: StrategyResult, strategies: Sequence[StrategyResult]) -> float:
    """Anteil der Hypothesen, die die Richtung von ``target`` teilen (0..1)."""
    if not strategies:
        return 0.0
    same = sum(1 for s in strategies if s.direction is target.direction)
    return same / len(strategies)


def compute_factors(
    strategy_result: StrategyResult,
    score_result: ScoreResult,
    risk_result: RiskResult,
    strategies: Sequence[StrategyResult],
    consensus_full_at: int = 2,
) -> dict[str, RecommendationFactor]:
    """Berechnet die sechs Entscheidungsfaktoren (je 0..100).

    Eine Empfehlung stützt sich nie ausschließlich auf den Score – hier fließen
    Strategie, Score, Risiko, Konsens, Marktqualität und Datenqualität ein.

    Der Konsens belohnt **Breite**: mehrere unabhängige Strategien in dieselbe
    Richtung erhöhen ihn (volle Wirkung ab ``consensus_full_at`` Strategien),
    widersprüchliche Strategien senken ihn. Eine einzelne Strategie erhält
    daher bewusst nur teilweisen Konsens.
    """
    same = sum(1 for s in strategies if s.direction is strategy_result.direction)
    total = len(strategies)
    agreement = same / total if total else 0.0
    breadth = min(1.0, same / consensus_full_at) if consensus_full_at > 0 else 1.0
    consensus_value = clamp_rating(agreement * breadth * 100.0)
    data_quality = float(score_result.component_scores.get("data_quality", 100.0))
    risk_adjusted = clamp_rating(100.0 - risk_result.overall_risk)
    return {
        "strategy": RecommendationFactor(
            "strategy",
            clamp_rating(strategy_result.strength),
            f"Strategie '{strategy_result.strategy_name}' Stärke "
            f"{strategy_result.strength:.0f}/100, Vertrauen {strategy_result.confidence:.2f}.",
        ),
        "score": RecommendationFactor(
            "score",
            clamp_rating(score_result.total_score),
            f"Score {score_result.total_score:.0f}/100.",
        ),
        "risk": RecommendationFactor(
            "risk",
            risk_adjusted,
            f"Risiko {risk_result.overall_risk:.0f}/100 "
            f"({risk_result.risk_level.value}) → risikobereinigt {risk_adjusted:.0f}.",
        ),
        "consensus": RecommendationFactor(
            "consensus",
            consensus_value,
            f"Konsens: {same}/{total} Hypothese(n) teilen die Richtung "
            f"(volle Breite ab {consensus_full_at}).",
        ),
        "market_quality": RecommendationFactor(
            "market_quality",
            clamp_rating(score_result.market_score),
            f"Marktqualität: Market Score {score_result.market_score:.0f}/100.",
        ),
        "data_quality": RecommendationFactor(
            "data_quality", clamp_rating(data_quality), f"Datenqualität {data_quality:.0f}/100."
        ),
    }


def compute_overall_rating(
    factors: Mapping[str, RecommendationFactor], weights: Mapping[str, float]
) -> float:
    """Gewichtetes Gesamtrating (0..100) aus den sechs Faktoren."""
    values = {name: factor.value for name, factor in factors.items()}
    return clamp_rating(weighted_sum(weights, values))


def compute_confidence(
    strategy_result: StrategyResult,
    factors: Mapping[str, RecommendationFactor],
    weights: Mapping[str, float],
) -> float:
    """Confidence 0..1 aus Strategie-Vertrauen, Konsens, Risiko und Datenqualität."""
    parts = {
        "strategy_confidence": clamp_confidence(strategy_result.confidence),
        "consensus": factors["consensus"].value / 100.0,
        "risk": factors["risk"].value / 100.0,
        "data_quality": factors["data_quality"].value / 100.0,
    }
    return clamp_confidence(sum(weights[key] * parts[key] for key in CONFIDENCE_WEIGHT_KEYS))


# --------------------------------------------------------------------------- #
# Stufen- und Handlungs-Zuordnung + Gates                                      #
# --------------------------------------------------------------------------- #


def level_severity(level: RecommendationLevel) -> int:
    """Ordnungszahl einer Stufe (AVOID=0 … STRONG_BUY=4)."""
    return _LEVEL_ORDER.index(level)


def cap_level(level: RecommendationLevel, cap: RecommendationLevel) -> RecommendationLevel:
    """Deckelt eine Stufe auf höchstens ``cap`` (No-Trade-Gate)."""
    return level if level_severity(level) <= level_severity(cap) else cap


def level_from_rating(rating: float, thresholds: Mapping[str, float]) -> RecommendationLevel:
    """Bildet ein Rating anhand der Schwellen auf eine Stufe ab."""
    if rating >= thresholds["strong_buy_min"]:
        return RecommendationLevel.STRONG_BUY
    if rating >= thresholds["buy_min"]:
        return RecommendationLevel.BUY
    if rating >= thresholds["watch_min"]:
        return RecommendationLevel.WATCH
    if rating >= thresholds["wait_min"]:
        return RecommendationLevel.WAIT
    return RecommendationLevel.AVOID


def action_for_level(level: RecommendationLevel) -> SuggestedAction:
    """Ordnet einer Stufe die vorgeschlagene Handlung zu (keine Ausführung)."""
    return _LEVEL_ACTION[level]


def is_neutral(direction: StrategyDirection) -> bool:
    """Ob die Richtung neutral ist (kein klarer Bias)."""
    return direction is StrategyDirection.NEUTRAL
