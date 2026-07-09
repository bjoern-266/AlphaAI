"""Ergebnistypen der Score Engine.

``ScoreResult`` bündelt die objektive Bewertung **einer** Hypothese;
``ScoreReport`` fasst alle Bewertungen eines Laufs samt Lauf-Metadaten
zusammen. Die Score Engine liefert ausschließlich diese Ergebnisse – keine
Kauf-/Verkaufsentscheidung, keine Positionsgröße, kein Risiko.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ScoreResult:
    """Objektive Bewertung einer Hypothese.

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


@dataclass(slots=True)
class ScoreReport:
    """Gesamtergebnis eines Score-Laufs für ein Symbol.

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
