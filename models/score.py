"""Domänenmodell: Score-Ergebnisse.

Enthält die unveränderlichen Datentypen der Score Engine: die
Komponentendefinition :data:`COMPONENT_NAMES`, die einzelne
:class:`ComponentScore`, die Modellausgabe :class:`ScoreModelOutput`, den
Eingabe-Kontext :class:`ScoreContext`, die Einzelbewertung
:class:`ScoreResult` und den Lauf-Report :class:`ScoreReport`.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.indicator`, :mod:`models.pattern`, :mod:`models.strategy`)
– **kein** Import aus ``engines``. Die Berechnungs-*Logik* (Komponenten,
Gewichtsvalidierung) bleibt in ``scores.base``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from models.indicator import IndicatorResult
from models.pattern import PatternReport
from models.strategy import StrategyResult

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


@dataclass(frozen=True, slots=True)
class ComponentScore:
    """Eine einzelne Score-Komponente (unveränderlich).

    Attributes:
        name: Komponentenname (aus :data:`COMPONENT_NAMES`).
        value: Wert 0..100.
        reason: Erklärung des Werts (Transparenz).
    """

    name: str
    value: float
    reason: str


@dataclass(frozen=True, slots=True)
class ScoreModelOutput:
    """Ergebnis eines einzelnen Score-Modells (unveränderlich).

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


@dataclass(frozen=True, slots=True)
class ScoreContext:
    """Eingabe für ein Score-Modell (unveränderlich).

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


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """Objektive Bewertung einer Hypothese (unveränderlich).

    Attributes:
        score_id: Stabiler Bezeichner der Bewertung.
        strategy_name: Name der bewerteten Strategie.
        hypothesis_id: Bezeichner der bewerteten Hypothese.
        total_score: Gesamtscore 0..100 (Weighted Score).
        confidence: Vertrauen 0..1 (Confidence Score).
        quality_score: Qualitäts-Score 0..100.
        consensus_score: Konsens-Score 0..100.
        market_score: Markt-Score 0..100.
        component_scores: Alle acht Komponenten (Name -> Wert 0..100).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen (u. a. alle Modell-Scores).
        timestamp: Zeitpunkt der Bewertung.
    """

    score_id: str
    strategy_name: str
    hypothesis_id: str
    total_score: float
    confidence: float
    quality_score: float
    consensus_score: float
    market_score: float
    component_scores: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class ScoreReport:
    """Gesamtergebnis eines Score-Laufs für ein Symbol (unveränderlich).

    Attributes:
        results: Alle Bewertungen (eine je Hypothese).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen (z. B. fehlende Hypothesen).
        metadata: Zusatzinformationen (Symbol, Timeframe, …).
    """

    results: list[ScoreResult] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_strategy(self, name: str) -> list[ScoreResult]:
        """Gibt alle Bewertungen einer bestimmten Strategie zurück."""
        return [r for r in self.results if r.strategy_name == name]

    def top(self, limit: int = 1) -> list[ScoreResult]:
        """Gibt die Bewertungen mit dem höchsten Gesamtscore zurück.

        Dies ist reine Sortierung/Anzeige – **keine** Handelsempfehlung.
        """
        return sorted(self.results, key=lambda r: r.total_score, reverse=True)[:limit]

    @property
    def score_count(self) -> int:
        """Anzahl erzeugter Bewertungen."""
        return len(self.results)
