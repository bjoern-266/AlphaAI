"""Domänenmodell: Paper Trading.

Enthält die unveränderlichen Datentypen des Paper-Trading-Frameworks. Paper
Trading **bewertet** ausschließlich, wie sich die **bestehenden**
AlphaAI-Empfehlungen unter (simulierten) Live-Marktbedingungen mit einem
**simulierten** Portfolio entwickeln. Es werden **niemals** echte Orders
ausgeführt, es gibt **keine** Broker-Anbindung und **keine** neue Handelsregel.

Enthaltene Typen:

* :class:`OrderAction` – OPEN/CLOSE/CANCEL/EXPIRE,
* :class:`PositionStatus` – OPEN/CLOSED/CANCELLED,
* :class:`CloseReason` – Grund eines Positions-Ausstiegs,
* :class:`PaperOrder` – eine simulierte Order (Audit/Journal),
* :class:`PaperPosition` – eine simulierte Position (vollständig nachvollziehbar),
* :class:`PaperTrade` – ein abgeschlossener simulierter Trade,
* :class:`JournalEntry` – ein automatischer Journal-Eintrag,
* :class:`PaperEquityPoint` – ein Punkt der Kapitalkurve,
* :class:`PaperStatistics` – aggregierte Handelsstatistik,
* :class:`PaperPerformance` – Kapital-/Drawdown-/Exposure-Kennzahlen,
* :class:`PaperTradingModelOutput` – Ausgabe eines Registry-Modells,
* :class:`PaperTradingContext` – Eingabe der Registry-Modelle,
* :class:`PaperTradingResult` – das Ergebnis je Position,
* :class:`PaperTradingReport` – der Lauf-Report.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.recommendation`) – **kein** Import aus ``engines``,
``paper_trading`` o. Ä. Die Logik liegt im Paket ``paper_trading``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from models.recommendation import Direction, RecommendationStrength


class OrderAction(Enum):
    """Aktion einer simulierten Order (keine echte Ausführung)."""

    OPEN = "open"
    CLOSE = "close"
    CANCEL = "cancel"
    EXPIRE = "expire"


class PositionStatus(Enum):
    """Status einer simulierten Position."""

    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class CloseReason(Enum):
    """Grund für den Ausstieg aus einer simulierten Position."""

    STOP = "stop"
    TAKE_PROFIT = "take_profit"
    EXPIRE = "expire"
    MANUAL = "manual"


@dataclass(frozen=True, slots=True)
class PaperOrder:
    """Eine simulierte Order (unveränderlich, für Audit/Journal).

    Es wird **keine** echte Order gesendet. Die Order dokumentiert lediglich eine
    Aktion (Eröffnen/Schließen/Stornieren/Verfallen) im simulierten Portfolio.

    Attributes:
        order_id: Stabiler Bezeichner der Order.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        position_id: Bezeichner der betroffenen Position.
        action: Aktion (OPEN/CLOSE/CANCEL/EXPIRE).
        direction: Handelsrichtung (LONG/SHORT/NEUTRAL).
        recommendation_strength: Stärke der zugrunde liegenden Empfehlung.
        price: Simulierter Preis der Order.
        shares: Stückzahl (Fractional Shares möglich).
        timestamp: Zeitpunkt der Order.
        reason: Menschenlesbarer Grund der Order.
    """

    order_id: str
    recommendation_id: str
    position_id: str
    action: OrderAction
    direction: Direction
    recommendation_strength: RecommendationStrength
    price: float
    shares: float
    timestamp: datetime | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True)
class PaperPosition:
    """Eine simulierte Position (unveränderlich, vollständig nachvollziehbar).

    Kennt Einstieg, Stop, Take-Profit, Trailing Stop (**vorbereitet**), Risiko und
    die zugrunde liegende Empfehlung (Richtung, Stärke, Begründungen). Aktualisiert
    wird sie ausschließlich über die Funktionen in ``paper_trading.position`` durch
    Erzeugen einer neuen Instanz (``dataclasses.replace``).

    Attributes:
        position_id: Stabiler Bezeichner der Position.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        symbol: Gehandeltes Symbol.
        direction: Handelsrichtung (LONG/SHORT).
        recommendation_strength: Stärke der zugrunde liegenden Empfehlung.
        status: Status (OPEN/CLOSED/CANCELLED).
        entry_price: Einstiegspreis.
        current_price: Aktueller (zuletzt bewerteter) Preis.
        exit_price: Ausstiegspreis (0.0 solange offen).
        stop_price: Stop-Loss-Preis.
        take_profit_price: Take-Profit-Preis.
        trailing_stop_price: Trailing-Stop-Preis (**vorbereitet**, 0.0 = inaktiv).
        shares: Stückzahl (Fractional Shares möglich).
        position_size: Positionswert bei Einstieg (Stück × Einstiegspreis).
        risk_amount: Riskierter Betrag in Kontowährung.
        entry_time: Zeitpunkt des Einstiegs.
        exit_time: Zeitpunkt des Ausstiegs (``None`` solange offen).
        close_reason: Grund des Ausstiegs (``None`` solange offen).
        pnl: Ergebnis in Kontowährung (unrealisiert wenn offen, realisiert wenn zu).
        pnl_pct: Ergebnis relativ zum Positionswert (Prozent).
        reasons: Begründungen der Empfehlung (Transparenz).
        warnings: Warnungen der Empfehlung.
        metadata: Zusatzinformationen.
    """

    position_id: str
    recommendation_id: str
    symbol: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    status: PositionStatus
    entry_price: float
    current_price: float
    stop_price: float
    take_profit_price: float
    shares: float
    position_size: float
    risk_amount: float
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    exit_price: float = 0.0
    trailing_stop_price: float = 0.0
    close_reason: CloseReason | None = None
    pnl: float = 0.0
    pnl_pct: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_open(self) -> bool:
        """Ob die Position offen ist."""
        return self.status is PositionStatus.OPEN

    @property
    def is_closed(self) -> bool:
        """Ob die Position geschlossen ist."""
        return self.status is PositionStatus.CLOSED

    @property
    def market_value(self) -> float:
        """Aktueller Marktwert der Position (Stück × aktueller Preis)."""
        return self.shares * self.current_price


@dataclass(frozen=True, slots=True)
class PaperTrade:
    """Ein abgeschlossener simulierter Trade (unveränderlich).

    Attributes:
        trade_id: Stabiler Bezeichner des Trades.
        position_id: Bezeichner der zugrunde liegenden Position.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        symbol: Gehandeltes Symbol.
        direction: Handelsrichtung.
        recommendation_strength: Stärke der Empfehlung.
        entry_price: Einstiegspreis.
        exit_price: Ausstiegspreis.
        shares: Stückzahl.
        pnl: Realisiertes Ergebnis (Kontowährung).
        pnl_pct: Ergebnis relativ zum Positionswert (Prozent).
        holding_time: Haltedauer (falls Zeitstempel vorhanden).
        close_reason: Grund des Ausstiegs.
        reasons: Begründungen der Empfehlung.
        warnings: Warnungen der Empfehlung.
    """

    trade_id: str
    position_id: str
    recommendation_id: str
    symbol: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    entry_price: float
    exit_price: float
    shares: float
    pnl: float
    pnl_pct: float
    holding_time: timedelta | None
    close_reason: CloseReason | None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_win(self) -> bool:
        """Ob der Trade ein Gewinn ist."""
        return self.pnl > 0.0

    @property
    def is_loss(self) -> bool:
        """Ob der Trade ein Verlust ist."""
        return self.pnl < 0.0


@dataclass(frozen=True, slots=True)
class JournalEntry:
    """Ein automatischer Journal-Eintrag (unveränderlich).

    Jeder simulierte Trade wird beim Eröffnen und Schließen dokumentiert.

    Attributes:
        entry_id: Stabiler Bezeichner des Eintrags.
        position_id: Bezeichner der betroffenen Position.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        action: Aktion (OPEN/CLOSE/CANCEL/EXPIRE).
        direction: Handelsrichtung.
        recommendation_strength: Stärke der Empfehlung.
        entry_price: Einstiegspreis.
        exit_price: Ausstiegspreis (0.0 bei Eröffnung).
        reason: Grund des Eintrags (z. B. „Stop getroffen").
        pnl: Ergebnis in Kontowährung (0.0 bei Eröffnung).
        reasons: Begründungen der Empfehlung.
        warnings: Warnungen der Empfehlung.
        timestamp: Zeitpunkt des Eintrags.
    """

    entry_id: str
    position_id: str
    recommendation_id: str
    action: OrderAction
    direction: Direction
    recommendation_strength: RecommendationStrength
    entry_price: float
    exit_price: float
    reason: str
    pnl: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class PaperEquityPoint:
    """Ein Punkt der Kapitalkurve des Paper-Portfolios (unveränderlich).

    Attributes:
        timestamp: Zeitpunkt des Punkts.
        equity: Kontostand (Kontowährung).
        drawdown_pct: Rückgang vom bisherigen Hoch in Prozent (0..100).
        exposure_pct: Anteil des Kapitals in offenen Positionen (Prozent).
        open_positions: Anzahl offener Positionen zu diesem Zeitpunkt.
    """

    timestamp: datetime | None
    equity: float
    drawdown_pct: float
    exposure_pct: float
    open_positions: int


@dataclass(frozen=True, slots=True)
class PaperStatistics:
    """Aggregierte Handelsstatistik des Paper-Portfolios (unveränderlich).

    Attributes:
        win_rate: Trefferquote 0..1.
        loss_rate: Verlustquote 0..1.
        profit_factor: Bruttogewinn / Bruttoverlust (``inf`` ohne Verluste).
        average_winner: Durchschnittlicher Gewinn (≥ 0).
        average_loser: Durchschnittlicher Verlust (≤ 0).
        average_holding_time: Durchschnittliche Haltedauer in Tagen.
        current_equity: Aktueller Kontostand.
        portfolio_return_pct: Gesamtrendite relativ zum Startkapital (Prozent).
        open_positions: Anzahl offener Positionen.
        closed_positions: Anzahl geschlossener Positionen.
    """

    win_rate: float = 0.0
    loss_rate: float = 0.0
    profit_factor: float = 0.0
    average_winner: float = 0.0
    average_loser: float = 0.0
    average_holding_time: float = 0.0
    current_equity: float = 0.0
    portfolio_return_pct: float = 0.0
    open_positions: int = 0
    closed_positions: int = 0


@dataclass(frozen=True, slots=True)
class PaperPerformance:
    """Kapital-, Drawdown- und Exposure-Kennzahlen (unveränderlich).

    Attributes:
        starting_capital: Startkapital.
        current_equity: Aktueller Kontostand.
        portfolio_return_pct: Gesamtrendite in Prozent.
        running_drawdown_pct: Aktueller Drawdown vom Hoch in Prozent.
        maximum_drawdown_pct: Maximaler Drawdown in Prozent.
        portfolio_exposure_pct: Aktuelles Exposure (Prozent des Kapitals).
        realized_pnl: Summe realisierter Ergebnisse.
        unrealized_pnl: Summe unrealisierter Ergebnisse (offene Positionen).
        equity_curve: Kapitalkurve.
    """

    starting_capital: float = 0.0
    current_equity: float = 0.0
    portfolio_return_pct: float = 0.0
    running_drawdown_pct: float = 0.0
    maximum_drawdown_pct: float = 0.0
    portfolio_exposure_pct: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    equity_curve: list[PaperEquityPoint] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PaperTradingModelOutput:
    """Ergebnis eines einzelnen Paper-Trading-Modells (unveränderlich).

    Attributes:
        name: Name des Modells.
        metrics: Berechnete numerische Kennzahlen (Name -> Wert).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Während der Berechnung gesammelte Warnungen.
        details: Zusätzliche, nicht rein numerische Aufschlüsselung.
    """

    name: str
    metrics: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PaperTradingContext:
    """Eingabe für ein Paper-Trading-Modell (unveränderlich).

    Die Engine ermittelt Positionen, Trades und Kapitalkurve **vorab** und stellt
    sie hier bereit, sodass jedes Modell unabhängig darauf zugreift.

    Attributes:
        symbol: Analysiertes Symbol.
        timeframe: Zeitebenen-Label.
        starting_capital: Startkapital (aus ``settings.toml``).
        current_equity: Aktueller Kontostand.
        positions: Alle Positionen (offen und geschlossen).
        trades: Alle abgeschlossenen Trades.
        equity_curve: Die Kapitalkurve.
        maximum_drawdown_pct: Maximaler Drawdown in Prozent.
        running_drawdown_pct: Aktueller Drawdown in Prozent.
        exposure_pct: Aktuelles Exposure in Prozent.
        realized_pnl: Summe realisierter Ergebnisse.
        unrealized_pnl: Summe unrealisierter Ergebnisse (offene Positionen).
        metadata: Zusatzinformationen.
    """

    symbol: str
    timeframe: str
    starting_capital: float
    current_equity: float
    positions: Sequence[PaperPosition]
    trades: Sequence[PaperTrade]
    equity_curve: Sequence[PaperEquityPoint]
    maximum_drawdown_pct: float = 0.0
    running_drawdown_pct: float = 0.0
    exposure_pct: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def open_positions(self) -> list[PaperPosition]:
        """Alle offenen Positionen."""
        return [p for p in self.positions if p.is_open]

    @property
    def closed_positions(self) -> list[PaperPosition]:
        """Alle geschlossenen Positionen."""
        return [p for p in self.positions if p.status is PositionStatus.CLOSED]


@dataclass(frozen=True, slots=True)
class PaperTradingResult:
    """Ergebnis je Position eines Paper-Trading-Laufs (unveränderlich).

    Vollständig nachvollziehbar über ``recommendation_id``, ``direction``,
    ``recommendation_strength``, ``reasons`` und ``warnings``.

    Attributes:
        paper_trading_id: Stabiler Bezeichner des Paper-Trading-Ergebnisses.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        symbol: Gehandeltes Symbol.
        direction: Handelsrichtung (LONG/SHORT).
        recommendation_strength: Stärke der Empfehlung.
        status: Status (OPEN/CLOSED/CANCELLED).
        entry_price: Einstiegspreis.
        current_price: Aktueller Preis.
        exit_price: Ausstiegspreis (0.0 solange offen).
        position_size: Positionswert bei Einstieg (Kontowährung).
        shares: Stückzahl (Fractional Shares möglich).
        fractional_shares: Ob Bruchstücke erlaubt sind (aus ``settings.toml``).
        entry_time: Zeitpunkt des Einstiegs.
        exit_time: Zeitpunkt des Ausstiegs (``None`` solange offen).
        pnl: Ergebnis in Kontowährung.
        pnl_pct: Ergebnis in Prozent.
        running_drawdown: Aktueller Portfolio-Drawdown in Prozent.
        maximum_drawdown: Maximaler Portfolio-Drawdown in Prozent.
        current_equity: Aktueller Kontostand des Portfolios.
        portfolio_exposure: Aktuelles Portfolio-Exposure in Prozent.
        close_reason: Grund des Ausstiegs (``None`` solange offen).
        reasons: Begründungen der Empfehlung (Transparenz).
        warnings: Warnungen der Empfehlung.
        metadata: Zusatzinformationen.
        timestamp: Zeitpunkt des Ergebnisses.
    """

    paper_trading_id: str
    recommendation_id: str
    symbol: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    status: PositionStatus
    entry_price: float
    current_price: float
    exit_price: float
    position_size: float
    shares: float
    fractional_shares: bool
    entry_time: datetime | None
    exit_time: datetime | None
    pnl: float
    pnl_pct: float
    running_drawdown: float
    maximum_drawdown: float
    current_equity: float
    portfolio_exposure: float
    close_reason: CloseReason | None = None
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class PaperTradingReport:
    """Gesamtergebnis eines Paper-Trading-Laufs (unveränderlich).

    Attributes:
        results: Alle Ergebnisse (eines je Position).
        statistics: Aggregierte Handelsstatistik.
        performance: Kapital-/Drawdown-/Exposure-Kennzahlen.
        journal: Automatisch geführtes Journal (Eröffnungen/Schließungen).
        orders: Alle simulierten Orders (Audit).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen (Symbol, Timeframe, …).
    """

    results: list[PaperTradingResult] = field(default_factory=list)
    statistics: PaperStatistics = field(default_factory=PaperStatistics)
    performance: PaperPerformance = field(default_factory=PaperPerformance)
    journal: list[JournalEntry] = field(default_factory=list)
    orders: list[PaperOrder] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_status(self, status: PositionStatus) -> list[PaperTradingResult]:
        """Gibt alle Ergebnisse eines Status zurück."""
        return [r for r in self.results if r.status is status]

    @property
    def open_results(self) -> list[PaperTradingResult]:
        """Alle offenen Ergebnisse."""
        return self.by_status(PositionStatus.OPEN)

    @property
    def closed_results(self) -> list[PaperTradingResult]:
        """Alle geschlossenen Ergebnisse."""
        return self.by_status(PositionStatus.CLOSED)

    @property
    def result_count(self) -> int:
        """Anzahl der Ergebnisse (Positionen)."""
        return len(self.results)
