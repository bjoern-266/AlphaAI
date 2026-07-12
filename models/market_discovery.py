"""Domänenmodell: Market Discovery.

Enthält die unveränderlichen Datentypen des Market-Discovery-Frameworks. Das
Framework durchsucht den gesamten konfigurierten Markt selbstständig, filtert
ungeeignete Kandidaten **vor** der vollständigen Analyse und priorisiert daraus
die objektiv besten Chancen. Es **berechnet niemals** Indikatoren, Muster,
Strategien, Scores, Risiken oder Empfehlungen – es nutzt ausschließlich bereits
vorhandene Ergebnisse.

Enthaltene Typen:

* :class:`MarketDefinition` – Beschreibung eines unterstützten Marktes,
* :class:`MarketSymbol` – ein Wert des Universums (Stammdaten + Vorfilter-Metriken),
* :class:`MarketUniverse` – die geladene Menge aller Werte,
* :class:`CandidateAnalysis` – die **bereits vorhandenen** Ergebnisse eines Werts,
* :class:`RejectedCandidate` – ein im Vorfilter verworfener Wert (mit Grund),
* :class:`DiscoveryOpportunity` – eine bewertete, eingeordnete Chance,
* :class:`DiscoveryStatistics` – Kennzahlen des Discovery-Laufs,
* :class:`DiscoveryReport` – der Lauf-Report.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.recommendation`, :mod:`models.analytics`,
:mod:`models.backtest`, :mod:`models.paper_trading`) – **kein** Import aus
``engines``, ``market_discovery`` o. Ä. Die Discovery-Logik liegt im Paket
``market_discovery``.
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
class MarketDefinition:
    """Beschreibung eines unterstützten Marktes (unveränderlich).

    Attributes:
        name: Stabiler Schlüssel (z. B. ``"nasdaq100"``) – zugleich Registry-Name.
        title: Anzeigename (z. B. ``"NASDAQ 100"``).
        country: Land des Marktes (z. B. ``"US"``/``"DE"``).
        exchange: Standard-Börsenplatz der Werte dieses Marktes.
    """

    name: str
    title: str = ""
    country: str = ""
    exchange: str = ""


@dataclass(frozen=True, slots=True)
class MarketSymbol:
    """Ein Wert des Universums (Stammdaten + Vorfilter-Metriken, unveränderlich).

    Die Metriken (Preis/Volumen/Historie/Handelbarkeit) sind **vorhandene**
    Stammdaten – **keine** berechneten Indikatoren.

    Attributes:
        ticker: Kürzel (Pflicht, eindeutig je Universum).
        company: Firmenname.
        sector: Branche.
        country: Land.
        exchange: Börsenplatz.
        market: Markt/Index-Schlüssel.
        price: Letzter Kurs (oder ``None``).
        volume: Handelsvolumen (Stück, oder ``None``).
        average_dollar_volume: Durchschnittlicher Umsatz (Liquidität, oder ``None``).
        history_days: Verfügbare Kurshistorie in Tagen (oder ``None``).
        tradable: Ob der Wert handelbar ist.
        delisted: Ob der Wert von der Börse genommen wurde.
        metadata: Zusatzinformationen.
    """

    ticker: str
    company: str = ""
    sector: str = ""
    country: str = ""
    exchange: str = ""
    market: str = ""
    price: float | None = None
    volume: float | None = None
    average_dollar_volume: float | None = None
    history_days: int | None = None
    tradable: bool = True
    delisted: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MarketUniverse:
    """Die geladene Menge aller Werte (unveränderlich).

    Attributes:
        name: Name des Universums.
        symbols: Alle Werte.
        markets: Enthaltene Markt-Schlüssel.
    """

    name: str = "universe"
    symbols: tuple[MarketSymbol, ...] = ()
    markets: tuple[str, ...] = ()

    @property
    def size(self) -> int:
        """Anzahl der Werte im Universum."""
        return len(self.symbols)

    def by_market(self, market: str) -> tuple[MarketSymbol, ...]:
        """Gibt alle Werte eines Marktes zurück."""
        return tuple(symbol for symbol in self.symbols if symbol.market == market)

    def tickers(self) -> tuple[str, ...]:
        """Gibt alle Ticker des Universums zurück."""
        return tuple(symbol.ticker for symbol in self.symbols)


@dataclass(frozen=True, slots=True)
class CandidateAnalysis:
    """Die **bereits vorhandenen** Ergebnisse eines Werts (unveränderlich).

    Alle Felder sind optional; fehlt eines, wird die zugehörige Score-Komponente
    im Market-Intelligence-Schritt schlicht ausgelassen. Es wird **nichts** neu
    berechnet – diese Ergebnisse stammen aus der bestehenden Pipeline.

    Attributes:
        recommendation: Die gewählte Empfehlung des Werts.
        analytics: Der Analytics-Report des Werts.
        backtest: Der Backtest-Report des Werts.
        paper_trading: Der Paper-Trading-Report des Werts.
    """

    recommendation: RecommendationResult | None = None
    analytics: AnalyticsReport | None = None
    backtest: BacktestReport | None = None
    paper_trading: PaperTradingReport | None = None


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    """Ein im Vorfilter verworfener Wert (unveränderlich).

    Attributes:
        ticker: Kürzel des verworfenen Werts.
        reason: Nachvollziehbarer Grund der Ablehnung.
    """

    ticker: str
    reason: str


@dataclass(frozen=True, slots=True)
class DiscoveryOpportunity:
    """Eine bewertete, eingeordnete Chance des Discovery-Laufs (unveränderlich).

    Die Bewertung stammt **unverändert** aus dem Market-Intelligence-Schritt; hier
    kommen lediglich die Stammdaten (u. a. Land) hinzu und der (ggf. nach Branchen
    ausbalancierte) Discovery-Rang.

    Attributes:
        ticker: Kürzel.
        company: Firmenname.
        sector: Branche.
        country: Land.
        exchange: Börsenplatz.
        market: Markt/Index.
        direction: Handelsrichtung (LONG/SHORT/NEUTRAL = „Watch").
        recommendation_strength: Empfehlungsstärke (unverändert).
        confidence: Vertrauen 0..1 (unverändert).
        risk: Risiko-Faktor 0..100 (höher = geringeres Risiko) oder ``None``.
        opportunity_score: Gewichtete Gesamtchance 0..100 (unverändert).
        rank: Platz in der finalen (ggf. ausbalancierten) Liste (1 = beste).
        summary: Kurzfassung.
        reasons: Begründungen (übernommen).
        warnings: Warnungen (übernommen).
        analytics_summary: Analytics-Kurzfassung.
        backtest_summary: Backtest-Kurzfassung.
        paper_trading_summary: Paper-Trading-Kurzfassung.
        timestamp: Erstellungszeitpunkt.
    """

    ticker: str
    company: str
    sector: str
    country: str
    exchange: str
    market: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    confidence: float
    risk: float | None
    opportunity_score: float
    rank: int = 0
    summary: str = ""
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    analytics_summary: str = ""
    backtest_summary: str = ""
    paper_trading_summary: str = ""
    timestamp: datetime | None = None

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
class DiscoveryStatistics:
    """Kennzahlen eines Discovery-Laufs (unveränderlich).

    Attributes:
        universe_count: Anzahl analysierter Aktien (Größe des Universums).
        rejected_count: Anzahl im Vorfilter verworfener Kandidaten.
        analyzed_count: Anzahl vollständiger Analysen (bewertete Chancen).
        long_count: Anzahl LONG-Chancen.
        short_count: Anzahl SHORT-Chancen.
        watch_count: Anzahl neutraler (Watch-)Chancen.
        average_score: Durchschnittlicher Opportunity Score (oder ``None``).
        average_risk: Durchschnittliches Risiko (oder ``None``).
        average_confidence: Durchschnittliche Confidence (oder ``None``).
        top_sectors: Häufigste Branchen als ``(Name, Anzahl)`` (absteigend).
        top_markets: Häufigste Märkte als ``(Name, Anzahl)`` (absteigend).
    """

    universe_count: int = 0
    rejected_count: int = 0
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
class DiscoveryReport:
    """Gesamtergebnis eines Market-Discovery-Laufs (unveränderlich).

    Attributes:
        opportunities: Die finalen Chancen in Ranking-Reihenfolge (Platz 1 zuerst).
        statistics: Aggregierte Kennzahlen.
        rejected: Die im Vorfilter verworfenen Kandidaten (mit Grund).
        markets: Durchsuchte Markt-Schlüssel.
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen.
        timestamp: Zeitpunkt des Laufs.
    """

    opportunities: tuple[DiscoveryOpportunity, ...] = ()
    statistics: DiscoveryStatistics = field(default_factory=DiscoveryStatistics)
    rejected: tuple[RejectedCandidate, ...] = ()
    markets: tuple[str, ...] = ()
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None

    @property
    def opportunity_count(self) -> int:
        """Anzahl der finalen Chancen."""
        return len(self.opportunities)

    def top(self, limit: int) -> tuple[DiscoveryOpportunity, ...]:
        """Gibt die besten ``limit`` Chancen zurück (reine Anzeige-Auswahl)."""
        return self.opportunities[: max(limit, 0)]

    def by_ticker(self, ticker: str) -> DiscoveryOpportunity | None:
        """Gibt die Chance zu einem Ticker zurück (oder ``None``)."""
        for opportunity in self.opportunities:
            if opportunity.ticker == ticker:
                return opportunity
        return None


__all__ = [
    "MarketDefinition",
    "MarketSymbol",
    "MarketUniverse",
    "CandidateAnalysis",
    "RejectedCandidate",
    "DiscoveryOpportunity",
    "DiscoveryStatistics",
    "DiscoveryReport",
]
