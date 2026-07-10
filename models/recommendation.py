"""Domänenmodell: Empfehlung – die letzte fachliche Entscheidungsschicht.

Enthält die unveränderlichen Datentypen der Recommendation Engine. **Richtung**
und **Qualität** sind vollständig getrennt: die Handelsrichtung
:class:`Direction` (LONG/SHORT/NEUTRAL) und die Empfehlungsstärke
:class:`RecommendationStrength` (VERY_HIGH … REJECT). Dazu die Handlung
:class:`SuggestedAction`, der Entscheidungsfaktor :class:`RecommendationFactor`,
die Modellausgabe :class:`RecommendationModelOutput`, der Eingabe-Kontext
:class:`RecommendationContext`, die Einzelempfehlung
:class:`RecommendationResult` und der Lauf-Report :class:`RecommendationReport`.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle und ``core`` – **kein** Import aus ``engines`` o. Ä. Die
Entscheidungs-*Logik* liegt in ``recommendation.base``.

AlphaAI trifft **keine** automatischen Handelsentscheidungen: Die
Recommendation Engine eröffnet **keine** Position, sendet **keine** Order und
kommuniziert **nicht** mit Brokern. ``LOW`` und ``REJECT`` sind vollwertige
Empfehlungen („Kein Trade ist besser als ein schlechter Trade."). Die Stärke
impliziert **niemals** eine Richtung – ein bärisches Setup ist ``SHORT`` mit
ggf. hoher Stärke, nie „BUY".
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from models.risk import RiskLevel, RiskResult
from models.score import ScoreResult
from models.strategy import StrategyDirection, StrategyResult

# Die sechs Faktoren, die jede Empfehlung getrennt berücksichtigt. Eine
# Empfehlung stützt sich nie ausschließlich auf den Score.
RECOMMENDATION_FACTOR_NAMES: tuple[str, ...] = (
    "strategy",
    "score",
    "risk",
    "consensus",
    "market_quality",
    "data_quality",
)


class Direction(Enum):
    """Handelsrichtung einer Empfehlung – **ausschließlich** die Richtung.

    Getrennt von der :class:`RecommendationStrength` (Qualität). Ein starkes
    bärisches Setup ist damit ``SHORT`` mit hoher Stärke – niemals „BUY".
    """

    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class RecommendationStrength(Enum):
    """Qualität/Stärke einer Empfehlung – **ausschließlich** die Güte.

    Beschreibt **nicht** die Richtung (die steht in :class:`Direction`) und
    impliziert bewusst kein BUY/SELL/LONG/SHORT.
    """

    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    REJECT = "reject"


class SuggestedAction(Enum):
    """Vorgeschlagene Handlung (keine automatische Ausführung, keine Richtung)."""

    OPEN = "open"
    WAIT = "wait"
    MONITOR = "monitor"
    SKIP = "skip"


# Reine Abbildung der Strategie-Richtung auf die Handelsrichtung – keine Logik.
_DIRECTION_MAP: dict[StrategyDirection, Direction] = {
    StrategyDirection.BULLISH: Direction.LONG,
    StrategyDirection.BEARISH: Direction.SHORT,
    StrategyDirection.NEUTRAL: Direction.NEUTRAL,
}


@dataclass(frozen=True, slots=True)
class RecommendationFactor:
    """Ein einzelner Entscheidungsfaktor (unveränderlich).

    Attributes:
        name: Faktorname (aus :data:`RECOMMENDATION_FACTOR_NAMES`).
        value: Wert 0..100 (höher = günstiger für die Empfehlung).
        reason: Erklärung des Werts (Transparenz).
    """

    name: str
    value: float
    reason: str


@dataclass(frozen=True, slots=True)
class RecommendationModelOutput:
    """Ergebnis eines einzelnen Recommendation-Modells (unveränderlich).

    Attributes:
        name: Name des Modells.
        value: Zahlenwert des Modells (Bedeutung modellabhängig).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Während der Berechnung gesammelte Warnungen.
        details: Zusätzliche Aufschlüsselung (z. B. Level/Action/Summary).
    """

    name: str
    value: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class RecommendationContext:
    """Eingabe für ein Recommendation-Modell (unveränderlich).

    Die Engine berechnet die sechs Faktoren, das Gesamtrating und die
    Basis-Confidence **vorab** (analog zum ScoreContext) und stellt sie hier
    bereit, sodass jedes Modell unabhängig darauf zugreift.

    Attributes:
        strategy_result: Die zugrunde liegende Hypothese.
        score_result: Die Score-Bewertung der Hypothese.
        risk_result: Die Risikobewertung der Hypothese.
        strategies: Alle Hypothesen des Laufs (für den Konsens).
        factors: Vorab berechnete Faktoren (Name -> RecommendationFactor).
        overall_rating: Vorab berechnetes Gesamtrating 0..100.
        base_confidence: Vorab berechnete Confidence 0..1.
        symbol: Symbolname.
        timeframe: Zeitebenen-Label.
    """

    strategy_result: StrategyResult
    score_result: ScoreResult
    risk_result: RiskResult
    strategies: Sequence[StrategyResult]
    factors: dict[str, RecommendationFactor]
    overall_rating: float
    base_confidence: float
    symbol: str = ""
    timeframe: str = "base"

    @property
    def direction(self) -> StrategyDirection:
        """Interne Richtung der Hypothese (Strategie-Enum, für die Gate-Logik)."""
        return self.strategy_result.direction

    @property
    def trade_direction(self) -> Direction:
        """Handelsrichtung als :class:`Direction` (LONG/SHORT/NEUTRAL)."""
        return _DIRECTION_MAP[self.strategy_result.direction]

    @property
    def risk_level(self) -> RiskLevel:
        """Risikostufe der Hypothese."""
        return self.risk_result.risk_level


@dataclass(frozen=True, slots=True)
class RecommendationResult:
    """Objektive Handlungsempfehlung einer Hypothese (unveränderlich).

    ``direction`` (Handelsrichtung) und ``recommendation_strength`` (Qualität)
    sind **vollständig getrennt**: Die Stärke impliziert nie eine Richtung; ein
    bärisches Setup ist ``SHORT`` mit ggf. hoher Stärke – niemals „BUY".

    Attributes:
        recommendation_id: Stabiler Bezeichner der Empfehlung.
        risk_id: Bezeichner der zugrunde liegenden Risikobewertung.
        score_id: Bezeichner der zugrunde liegenden Score-Bewertung.
        hypothesis_id: Bezeichner der bewerteten Hypothese.
        direction: Handelsrichtung (LONG/SHORT/NEUTRAL) – ausschließlich Richtung.
        recommendation_strength: Qualität/Stärke (VERY_HIGH … REJECT) –
            ausschließlich Güte, keine Richtung.
        confidence: Vertrauen 0..1 in die Empfehlung.
        overall_rating: Gesamtbewertung 0..100.
        suggested_action: Vorgeschlagene Handlung (keine Ausführung).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Gesammelte Warnungen.
        summary: Menschenlesbare Kurzfassung.
        metadata: Zusatzinformationen (u. a. Faktoren, Modellwerte).
        timestamp: Zeitpunkt der Empfehlung.
    """

    recommendation_id: str
    risk_id: str
    score_id: str
    hypothesis_id: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    confidence: float
    overall_rating: float
    suggested_action: SuggestedAction
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class RecommendationReport:
    """Gesamtergebnis eines Recommendation-Laufs (unveränderlich).

    Attributes:
        results: Alle Empfehlungen (eine je Hypothese).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen (z. B. fehlende Reports).
        metadata: Zusatzinformationen (Symbol, Timeframe, …).
    """

    results: list[RecommendationResult] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_strength(self, strength: RecommendationStrength) -> list[RecommendationResult]:
        """Gibt alle Empfehlungen einer Stärke zurück."""
        return [r for r in self.results if r.recommendation_strength is strength]

    def by_direction(self, direction: Direction) -> list[RecommendationResult]:
        """Gibt alle Empfehlungen einer Handelsrichtung zurück."""
        return [r for r in self.results if r.direction is direction]

    def by_action(self, action: SuggestedAction) -> list[RecommendationResult]:
        """Gibt alle Empfehlungen einer vorgeschlagenen Handlung zurück."""
        return [r for r in self.results if r.suggested_action is action]

    def top(self, limit: int = 1) -> list[RecommendationResult]:
        """Gibt die höchstbewerteten Empfehlungen zurück.

        Reine Sortierung/Anzeige – **keine** automatische Handelsentscheidung.
        """
        return sorted(self.results, key=lambda r: r.overall_rating, reverse=True)[:limit]

    @property
    def recommendation_count(self) -> int:
        """Anzahl erzeugter Empfehlungen."""
        return len(self.results)
