"""Domänenmodell: Market Intelligence & Opportunities.

Enthält die unveränderlichen Datentypen des Market-Intelligence-Frameworks. Das
Framework **bewertet ausschließlich bereits vorhandene Ergebnisse** (Empfehlung,
Risiko, Analytics, Backtesting, Paper Trading) und priorisiert daraus die
objektiv besten Chancen. Es trifft **keine** Handelsentscheidung, verändert
**keine** bestehenden Ergebnisse, erzeugt **keine** neue Handelsregel und enthält
**keine** Machine-Learning-Komponenten.

Enthaltene Typen:

* :class:`MarketCandidate` – die Eingabe je Aktie (bündelt die bereits
  vorhandenen Reports einer Aktie),
* :class:`OpportunityModelOutput` – der Score-Beitrag eines einzelnen
  Bewertungsmodells (Recommendation/Risk/Analytics/Backtest/Paper Trading),
* :class:`Opportunity` – eine bewertete und eingeordnete Chance,
* :class:`OpportunityStatistics` – Kennzahlen über alle Chancen,
* :class:`OpportunityExplanation` – die transparente Herleitung einer Chance,
* :class:`Watchlist` – eine erzeugte Watchlist,
* :class:`OpportunityReport` – der Lauf-Report,
* :class:`MarketIntelligenceContext` – die Eingabe der Bewertungsmodelle.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.recommendation`, :mod:`models.analytics`,
:mod:`models.backtest`, :mod:`models.paper_trading`) – **kein** Import aus
``engines``, ``market_intelligence`` o. Ä. Die Bewertungs-/Ranking-Logik liegt
im Paket ``market_intelligence``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from models.analytics import AnalyticsReport
from models.backtest import BacktestReport
from models.paper_trading import PaperTradingReport
from models.recommendation import Direction, RecommendationResult, RecommendationStrength


@dataclass(frozen=True, slots=True)
class MarketCandidate:
    """Eine zu bewertende Aktie mit ihren **bereits vorhandenen** Ergebnissen.

    Alle Reports sind optional; fehlt einer, wird die zugehörige Score-Komponente
    schlicht ausgelassen (die Chance wird über die verbleibenden Komponenten
    bewertet – es wird **nichts** ersatzweise berechnet).

    Attributes:
        ticker: Kürzel der Aktie (Pflicht, eindeutig je Lauf).
        company: Firmenname (Anzeige).
        market: Markt/Index (z. B. ``"NASDAQ"``).
        sector: Branche.
        exchange: Börsenplatz.
        recommendation: Die gewählte Empfehlung dieser Aktie (aus einem
            :class:`~models.recommendation.RecommendationReport`).
        analytics: Der Analytics-Report dieser Aktie.
        backtest: Der Backtest-Report dieser Aktie.
        paper_trading: Der Paper-Trading-Report dieser Aktie.
        pattern_summary: Bereits vorhandene Muster-Kurzfassung (Text).
        strategy_summary: Bereits vorhandene Strategie-Kurzfassung (Text).
        metadata: Zusatzinformationen.
    """

    ticker: str
    company: str = ""
    market: str = ""
    sector: str = ""
    exchange: str = ""
    recommendation: RecommendationResult | None = None
    analytics: AnalyticsReport | None = None
    backtest: BacktestReport | None = None
    paper_trading: PaperTradingReport | None = None
    pattern_summary: str = ""
    strategy_summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OpportunityModelOutput:
    """Score-Beitrag eines einzelnen Bewertungsmodells (unveränderlich).

    Attributes:
        name: Name des Modells (= Schlüssel in ``market_intelligence_rules.toml``).
        score: Beitrag 0..100 (aus einer **bestehenden** Kennzahl abgeleitet).
        weight: Gewicht des Beitrags (aus der Regeldatei).
        available: Ob die Quelle vorhanden war (sonst wird der Beitrag ignoriert).
        reasons: Nachvollziehbare Begründungen (Transparenz, keine Blackbox).
        warnings: Gesammelte Warnungen.
        details: Zusätzliche Aufschlüsselung.
    """

    name: str
    score: float
    weight: float
    available: bool = True
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Opportunity:
    """Eine bewertete und eingeordnete Chance (unveränderlich).

    Der ``opportunity_score`` ist **kein neues Bewertungssystem**: er ist die
    gewichtete Zusammenfassung der **bestehenden** Signale (Recommendation, Risk,
    Analytics, Backtesting, Paper Trading). Richtung, Stärke, Confidence, Rating
    und Risiko werden **unverändert** aus der Empfehlung übernommen.

    Attributes:
        ticker: Kürzel der Aktie.
        company: Firmenname.
        market: Markt/Index.
        direction: Handelsrichtung (LONG/SHORT/NEUTRAL = „Watch").
        recommendation_strength: Stärke der Empfehlung (unverändert).
        confidence: Vertrauen 0..1 (unverändert).
        overall_rating: Gesamtbewertung 0..100 (unverändert).
        risk: Risiko-Faktor 0..100 (höher = geringeres Risiko) oder ``None``.
        opportunity_score: Gewichtete Gesamtchance 0..100.
        opportunity_rank: Platz im Ranking (1 = beste Chance; 0 = unzugeordnet).
        summary: Menschenlesbare Kurzfassung.
        sector: Branche.
        exchange: Börsenplatz.
        reasons: Gesammelte Begründungen (aus den Quellen übernommen).
        warnings: Gesammelte Warnungen.
        pattern_summary: Muster-Kurzfassung.
        strategy_summary: Strategie-Kurzfassung.
        analytics_summary: Analytics-Kurzfassung.
        backtest_summary: Backtest-Kurzfassung.
        paper_trading_summary: Paper-Trading-Kurzfassung.
        components: Roh-Score je Komponente (Transparenz).
        timestamp: Erstellungszeitpunkt.
        metadata: Zusatzinformationen.
    """

    ticker: str
    company: str
    market: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    confidence: float
    overall_rating: float
    risk: float | None
    opportunity_score: float
    opportunity_rank: int = 0
    summary: str = ""
    sector: str = ""
    exchange: str = ""
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    pattern_summary: str = ""
    strategy_summary: str = ""
    analytics_summary: str = ""
    backtest_summary: str = ""
    paper_trading_summary: str = ""
    components: dict[str, float] = field(default_factory=dict)
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_long(self) -> bool:
        """Ob die Chance eine LONG-Ausrichtung hat."""
        return self.direction is Direction.LONG

    @property
    def is_short(self) -> bool:
        """Ob die Chance eine SHORT-Ausrichtung hat."""
        return self.direction is Direction.SHORT

    @property
    def is_watch(self) -> bool:
        """Ob die Chance neutral ist (Beobachtung/„Watch")."""
        return self.direction is Direction.NEUTRAL


@dataclass(frozen=True, slots=True)
class OpportunityStatistics:
    """Kennzahlen über alle bewerteten Chancen (unveränderlich).

    Attributes:
        analyzed_count: Anzahl bewerteter Aktien.
        long_count: Anzahl LONG-Chancen.
        short_count: Anzahl SHORT-Chancen.
        watch_count: Anzahl neutraler (Watch-)Chancen.
        average_score: Durchschnittlicher Opportunity Score (oder ``None``).
        average_risk: Durchschnittliches Risiko (oder ``None``).
        average_confidence: Durchschnittliche Confidence (oder ``None``).
        top_sectors: Häufigste Branchen als ``(Name, Anzahl)`` (absteigend).
        top_markets: Häufigste Märkte als ``(Name, Anzahl)`` (absteigend).
    """

    analyzed_count: int = 0
    long_count: int = 0
    short_count: int = 0
    watch_count: int = 0
    average_score: float | None = None
    average_risk: float | None = None
    average_confidence: float | None = None
    top_sectors: tuple[tuple[str, int], ...] = ()
    top_markets: tuple[tuple[str, int], ...] = ()


@dataclass(frozen=True, slots=True)
class OpportunityExplanation:
    """Transparente Herleitung einer Chance (unveränderlich, keine Blackbox).

    Attributes:
        ticker: Kürzel der Aktie.
        rank: Platz im Ranking.
        opportunity_score: Gesamtchance 0..100.
        headline: Kernaussage (z. B. „Warum Platz 1?").
        factors: Entscheidende Faktoren (die stärksten Komponenten).
        risks: Bestehende Risiken/Warnungen.
        why_not_higher: Warum die Chance nicht höher steht (Vergleich nach oben).
    """

    ticker: str
    rank: int
    opportunity_score: float
    headline: str
    factors: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    why_not_higher: str = ""


@dataclass(frozen=True, slots=True)
class Watchlist:
    """Eine erzeugte Watchlist (unveränderlich).

    Attributes:
        name: Name der Watchlist (z. B. ``"top"``/``"long"``/``"short"``).
        title: Anzeigetitel.
        tickers: Enthaltene Kürzel (in Ranking-Reihenfolge).
    """

    name: str
    title: str = ""
    tickers: tuple[str, ...] = ()

    @property
    def size(self) -> int:
        """Anzahl der Einträge."""
        return len(self.tickers)


@dataclass(frozen=True, slots=True)
class OpportunityReport:
    """Gesamtergebnis eines Market-Intelligence-Laufs (unveränderlich).

    Attributes:
        opportunities: Alle Chancen in Ranking-Reihenfolge (Platz 1 zuerst).
        statistics: Aggregierte Kennzahlen.
        explanations: Herleitung je Ticker.
        watchlists: Erzeugte Watchlists (Name -> Watchlist).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen.
        timestamp: Zeitpunkt des Laufs.
    """

    opportunities: tuple[Opportunity, ...] = ()
    statistics: OpportunityStatistics = field(default_factory=OpportunityStatistics)
    explanations: dict[str, OpportunityExplanation] = field(default_factory=dict)
    watchlists: dict[str, Watchlist] = field(default_factory=dict)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None

    @property
    def opportunity_count(self) -> int:
        """Anzahl bewerteter Chancen."""
        return len(self.opportunities)

    def top(self, limit: int) -> tuple[Opportunity, ...]:
        """Gibt die besten ``limit`` Chancen zurück (reine Anzeige-Auswahl)."""
        return self.opportunities[: max(limit, 0)]

    def by_rank(self, rank: int) -> Opportunity | None:
        """Gibt die Chance mit einem bestimmten Rang zurück (oder ``None``)."""
        for opportunity in self.opportunities:
            if opportunity.opportunity_rank == rank:
                return opportunity
        return None

    def by_ticker(self, ticker: str) -> Opportunity | None:
        """Gibt die Chance zu einem Ticker zurück (oder ``None``)."""
        for opportunity in self.opportunities:
            if opportunity.ticker == ticker:
                return opportunity
        return None


@dataclass(frozen=True, slots=True)
class MarketIntelligenceContext:
    """Eingabe für ein Bewertungsmodell (unveränderlich).

    Attributes:
        candidate: Die zu bewertende Aktie mit ihren vorhandenen Reports.
        config: Gemeinsame Konfiguration (Score-Grenzen etc. aus der Regeldatei).
    """

    candidate: MarketCandidate
    config: dict[str, Any] = field(default_factory=dict)


__all__ = [
    "MarketCandidate",
    "OpportunityModelOutput",
    "Opportunity",
    "OpportunityStatistics",
    "OpportunityExplanation",
    "Watchlist",
    "OpportunityReport",
    "MarketIntelligenceContext",
]
