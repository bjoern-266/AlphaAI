"""Gemeinsame Schnittstelle, Typen und Hilfsmittel für Score-Modelle.

Alle Score-Modelle implementieren :class:`BaseScoreModel` und geben ihr
Ergebnis als :class:`ScoreModelOutput` zurück. Die Typen liegen bewusst hier
(nicht in ``engines``), damit kein Import-Zyklus zwischen ``scores`` und
``engines`` entsteht.

Hier stehen außerdem die **Komponenten-Berechnung** (acht Komponenten) und die
**Gewichtsvalidierung** – gemeinsame Hilfsmittel, kein eigenes Score-Modell,
sodass kein Modell von einem anderen Modell abhängt.

Die Score-Modelle berechnen ausschließlich objektive Scores. Sie treffen keine
Kauf-/Verkaufsentscheidung, erzeugen keine Positionsgröße und kein Risiko.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # nur für Typannotationen – kein Laufzeit-Import aus engines
    from engines.indicator_result import IndicatorResult
    from engines.pattern_result import PatternReport
    from strategies.base import StrategyResult

# Die acht Komponenten, die jeder Score getrennt speichert.
COMPONENT_NAMES: tuple[str, ...] = (
    "trend",
    "momentum",
    "pattern_strength",
    "pattern_confidence",
    "indicator_quality",
    "market_context",
    "volume_quality",
    "data_quality",
)

# Standard-Indikatorsatz zur Bewertung der Indikatorqualität.
_EXPECTED_INDICATORS: frozenset[str] = frozenset(
    {
        "ema",
        "rsi",
        "atr",
        "vwap",
        "macd",
        "relative_volume",
        "adx",
        "bollinger",
        "stochastic",
        "obv",
        "volume_profile",
    }
)


class ScoreParameterError(ValueError):
    """Wird ausgelöst, wenn Gewichte fehlen, ungültig sind oder ≠ 100 % ergeben."""


@dataclass(slots=True)
class ComponentScore:
    """Eine einzelne Score-Komponente.

    Attributes:
        name: Komponentenname (aus :data:`COMPONENT_NAMES`).
        value: Wert 0..100.
        reason: Erklärung des Werts (Transparenz).
    """

    name: str
    value: float
    reason: str


@dataclass(slots=True)
class ScoreModelOutput:
    """Ergebnis eines einzelnen Score-Modells.

    Attributes:
        name: Name des Score-Modells.
        value: Score-Wert (Wertebereich modellabhängig, z. B. 0..100 oder 0..1).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Während der Berechnung gesammelte Warnungen.
        details: Zusätzliche Aufschlüsselung (z. B. Beitrag je Komponente).
    """

    name: str
    value: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScoreContext:
    """Eingabe für ein Score-Modell.

    Attributes:
        strategy_result: Die zu bewertende Hypothese.
        indicators: Ergebnis der Indicator Engine.
        patterns: Ergebnis der Pattern Engine.
        hypotheses: Alle Hypothesen des Laufs (für Konsens).
        components: Vorab berechnete Komponenten (Name -> ComponentScore).
        symbol: Symbolname.
        timeframe: Zeitebenen-Label.
    """

    strategy_result: StrategyResult
    indicators: IndicatorResult
    patterns: PatternReport
    hypotheses: Sequence[StrategyResult]
    components: dict[str, ComponentScore]
    symbol: str = ""
    timeframe: str = "base"


class BaseScoreModel(ABC):
    """Basisklasse für alle Score-Modelle.

    Attributes:
        name: Eindeutiger Modellname.
        value_range: Beschreibung des Wertebereichs (Dokumentation).
    """

    name: str = "base"
    value_range: str = "0..100"

    @abstractmethod
    def compute(self, context: ScoreContext, params: Mapping[str, Any]) -> ScoreModelOutput:
        """Berechnet den Score aus Komponenten und Kontext.

        Args:
            context: Hypothese, Komponenten und weitere Eingaben.
            params: Gewichte/Parameter des Modells (aus der Konfiguration).

        Returns:
            Ein :class:`ScoreModelOutput`.
        """
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# Gewichtsvalidierung (gemeinsames Hilfsmittel)                                #
# --------------------------------------------------------------------------- #


def validate_weights(
    params: Mapping[str, Any], expected: Sequence[str], model: str, tolerance: float = 0.001
) -> dict[str, float]:
    """Prüft und normalisiert die Gewichte eines Modells.

    Prüft: keine fehlenden Komponenten, keine unbekannten Schlüssel, jedes
    Gewicht in [0, 1] und Summe = 100 % (± ``tolerance``).

    Raises:
        ScoreParameterError: Bei fehlenden Komponenten, ungültigen Gewichten
            oder einer Gewichtssumme ungleich 100 %.
    """
    missing = [key for key in expected if key not in params]
    if missing:
        raise ScoreParameterError(f"Modell '{model}': fehlende Komponenten/Gewichte {missing}.")
    unknown = [key for key in params if key not in expected]
    if unknown:
        raise ScoreParameterError(f"Modell '{model}': unbekannte Gewichte {unknown}.")

    weights: dict[str, float] = {}
    for key in expected:
        value = params[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0.0 <= value <= 1.0
        ):
            raise ScoreParameterError(
                f"Modell '{model}': ungültiges Gewicht '{key}'={value} (erwartet 0..1)."
            )
        weights[key] = float(value)

    total = sum(weights.values())
    if abs(total - 1.0) > tolerance:
        raise ScoreParameterError(
            f"Modell '{model}': Gewichte summieren zu {total * 100:.1f} % (≠ 100 %)."
        )
    return weights


def weighted_sum(weights: Mapping[str, float], components: Mapping[str, ComponentScore]) -> float:
    """Bildet die gewichtete Summe der Komponentenwerte (0..100)."""
    return float(sum(weight * components[name].value for name, weight in weights.items()))


def consensus_fraction(target: StrategyResult, hypotheses: Sequence[StrategyResult]) -> float:
    """Anteil der Hypothesen, die die Richtung von ``target`` teilen (0..1)."""
    if not hypotheses:
        return 0.0
    same = sum(1 for h in hypotheses if h.direction is target.direction)
    return same / len(hypotheses)


# --------------------------------------------------------------------------- #
# Komponenten-Berechnung (gemeinsames Hilfsmittel, kein Score-Modell)          #
# --------------------------------------------------------------------------- #


def _clamp(value: float) -> float:
    """Begrenzt einen Wert auf 0..100."""
    return float(min(100.0, max(0.0, value)))


def _component_trend(strategy: StrategyResult, indicators: IndicatorResult) -> ComponentScore:
    """Trendkomponente aus EMA-Fächer und ADX in Bezug auf die Richtung."""
    ema20, ema50, ema200, adx = (
        indicators.ema20,
        indicators.ema50,
        indicators.ema200,
        indicators.adx,
    )
    if None in (ema20, ema50, ema200, adx):
        return ComponentScore("trend", 50.0, "Trend: unvollständige Daten (neutral).")
    up = ema20 > ema50 > ema200
    down = ema20 < ema50 < ema200
    aligned = (up and strategy.direction.value == "bullish") or (
        down and strategy.direction.value == "bearish"
    )
    base = _clamp(adx)
    value = base if aligned else base * 0.5
    fit = "aligned" if aligned else "nicht aligned"
    return ComponentScore("trend", value, f"Trend: EMA-Fächer {fit}, ADX {adx:.1f}.")


def _component_momentum(strategy: StrategyResult, indicators: IndicatorResult) -> ComponentScore:
    """Momentumkomponente aus RSI und MACD-Histogramm."""
    rsi, hist = indicators.rsi14, indicators.macd_histogram
    if rsi is None or hist is None:
        return ComponentScore("momentum", 50.0, "Momentum: unvollständige Daten (neutral).")
    bull = rsi >= 50 and hist > 0
    bear = rsi <= 50 and hist < 0
    aligned = (bull and strategy.direction.value == "bullish") or (
        bear and strategy.direction.value == "bearish"
    )
    base = _clamp(abs(rsi - 50.0) * 2.0)
    value = base if aligned else base * 0.5
    fit = "bestätigt" if aligned else "gegenläufig"
    return ComponentScore("momentum", value, f"Momentum: RSI {rsi:.1f}, Histogramm {fit}.")


def _matching_patterns(strategy: StrategyResult, patterns: PatternReport) -> list[Any]:
    """Muster, deren Richtung zur Hypothese passt."""
    return [p for p in patterns.results if p.direction.value == strategy.direction.value]


def _component_pattern_strength(
    strategy: StrategyResult, patterns: PatternReport
) -> ComponentScore:
    """Musterstärke: mittlere Stärke der richtungsgleichen Muster."""
    matching = _matching_patterns(strategy, patterns)
    if not matching:
        return ComponentScore("pattern_strength", 30.0, "Pattern Strength: keine passenden Muster.")
    value = _clamp(sum(p.strength for p in matching) / len(matching))
    return ComponentScore(
        "pattern_strength", value, f"Pattern Strength: Ø aus {len(matching)} Muster(n)."
    )


def _component_pattern_confidence(
    strategy: StrategyResult, patterns: PatternReport
) -> ComponentScore:
    """Musterkonfidenz: mittlere Confidence der richtungsgleichen Muster (0..100)."""
    matching = _matching_patterns(strategy, patterns)
    if not matching:
        return ComponentScore("pattern_confidence", 50.0, "Pattern Confidence: keine Muster.")
    value = _clamp(sum(p.confidence for p in matching) / len(matching) * 100.0)
    return ComponentScore(
        "pattern_confidence", value, f"Pattern Confidence: Ø aus {len(matching)} Muster(n)."
    )


def _component_indicator_quality(indicators: IndicatorResult) -> ComponentScore:
    """Indikatorqualität: Anteil verfügbarer Standard-Indikatoren."""
    present = _EXPECTED_INDICATORS & set(indicators.outputs)
    value = len(present) / len(_EXPECTED_INDICATORS) * 100.0
    if not indicators.valid:
        value *= 0.5
    return ComponentScore(
        "indicator_quality",
        _clamp(value),
        f"Indicator Quality: {len(present)}/{len(_EXPECTED_INDICATORS)} Indikatoren"
        + ("" if indicators.valid else ", Ergebnis ungültig"),
    )


def _component_market_context(strategy: StrategyResult, patterns: PatternReport) -> ComponentScore:
    """Marktkontext: Übereinstimmung mit Markt-/Trendstruktur."""
    structure = patterns.by_name("market_structure") + patterns.by_name("trend_structure")
    if not structure:
        return ComponentScore("market_context", 50.0, "Market Context: keine Strukturdaten.")
    latest = structure[-1]
    aligned = latest.direction.value == strategy.direction.value
    value = 80.0 if aligned else 30.0
    fit = "im Einklang" if aligned else "gegenläufig"
    return ComponentScore("market_context", value, f"Market Context: Struktur {fit}.")


def _component_volume_quality(indicators: IndicatorResult) -> ComponentScore:
    """Volumenqualität aus relativem Volumen (rvol 2.0 -> 100)."""
    rvol = indicators.relative_volume
    if rvol is None:
        return ComponentScore("volume_quality", 50.0, "Volume Quality: kein relatives Volumen.")
    value = _clamp(rvol * 50.0)
    return ComponentScore("volume_quality", value, f"Volume Quality: rel. Volumen {rvol:.2f}.")


def _component_data_quality(indicators: IndicatorResult, patterns: PatternReport) -> ComponentScore:
    """Datenqualität aus Gültigkeit, Historie und Warnungen."""
    value = 100.0
    notes: list[str] = []
    if not indicators.valid:
        value -= 30.0
        notes.append("Indikatoren ungültig")
    if not patterns.valid:
        value -= 30.0
        notes.append("Muster ungültig")
    candles = int(indicators.metadata.get("candle_count", 0))
    if candles < 30:
        value -= 20.0
        notes.append(f"nur {candles} Kerzen")
    warn_count = len(indicators.warnings) + len(patterns.warnings)
    value -= min(20.0, warn_count * 2.0)
    reason = "Data Quality: " + ("; ".join(notes) if notes else "vollständig")
    return ComponentScore("data_quality", _clamp(value), reason)


def compute_components(
    strategy: StrategyResult, indicators: IndicatorResult, patterns: PatternReport
) -> dict[str, ComponentScore]:
    """Berechnet alle acht Komponenten für eine Hypothese.

    Returns:
        Zuordnung Komponentenname -> :class:`ComponentScore` (alle acht).
    """
    return {
        "trend": _component_trend(strategy, indicators),
        "momentum": _component_momentum(strategy, indicators),
        "pattern_strength": _component_pattern_strength(strategy, patterns),
        "pattern_confidence": _component_pattern_confidence(strategy, patterns),
        "indicator_quality": _component_indicator_quality(indicators),
        "market_context": _component_market_context(strategy, patterns),
        "volume_quality": _component_volume_quality(indicators),
        "data_quality": _component_data_quality(indicators, patterns),
    }
