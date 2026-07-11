"""Domänenmodell: Trading Intelligence & Analytics.

Enthält die unveränderlichen Datentypen des Analytics-Frameworks. Das Framework
**analysiert ausschließlich** bereits vorhandene Daten aus Backtesting und Paper
Trading und erzeugt daraus **objektive, reproduzierbare Kennzahlen**. Es trifft
**keine** Handelsentscheidung, verändert **keine** bestehenden Ergebnisse und
erzeugt **keine** neuen Empfehlungen – es liefert ausschließlich Statistiken.

Enthaltene Typen:

* :class:`AnalyticsTrade` – ein normalisierter Trade (aus Backtest **oder** Paper
  Trading), damit alle Analysen einheitlich darauf arbeiten,
* :class:`GroupStatistics` – Kennzahlen einer Gruppe (z. B. LONG, eine Strategie,
  ein Risiko-Level),
* :class:`AnalyticsModelOutput` – Ausgabe eines einzelnen Analysemodells,
* :class:`AnalyticsContext` – Eingabe der Analysemodelle,
* :class:`AnalyticsResult` – das gebündelte Analyseergebnis,
* :class:`AnalyticsReport` – der Lauf-Report.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle (:mod:`models.recommendation`, :mod:`models.paper_trading`) – **kein**
Import aus ``engines``, ``analytics`` o. Ä. Die Berechnungslogik liegt im Paket
``analytics``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from models.paper_trading import JournalEntry
from models.recommendation import Direction, RecommendationStrength


@dataclass(frozen=True, slots=True)
class AnalyticsTrade:
    """Ein normalisierter Trade für die Analyse (unveränderlich).

    Vereinheitlicht Backtest- und Paper-Trading-Trades, sodass alle Analysen auf
    demselben Typ arbeiten. Nicht in allen Quellen vorhandene Größen sind neutral
    belegt (``0.0`` bzw. ``None``); daraus abgeleitete Dimensionen (Strategie,
    Risiko-Level, Score) werden aus ``recommendation_id``/``reasons`` gewonnen und
    sind damit vollständig nachvollziehbar.

    Attributes:
        source: Herkunft (``"backtest"`` oder ``"paper_trading"``).
        trade_id: Bezeichner des Quell-Trades.
        symbol: Gehandeltes Symbol.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        direction: Handelsrichtung (LONG/SHORT/NEUTRAL).
        recommendation_strength: Stärke der Empfehlung.
        strategy: Aus der ``recommendation_id`` abgeleiteter Strategiename.
        risk_level: Aus den ``reasons`` abgeleitetes Risiko-Level
            (``"low"``/``"medium"``/``"high"``/``"unbekannt"``).
        score: Aus den ``reasons`` abgeleiteter Score (0..100) oder ``None``.
        pnl: Ergebnis in Kontowährung.
        pnl_pct: Ergebnis relativ zum Positionswert (Prozent).
        return_on_risk: Ergebnis als R-Vielfaches (0.0, falls unbekannt).
        risk_reward: Geplantes Chance-Risiko-Verhältnis (0.0, falls unbekannt).
        holding_time: Haltedauer (falls Zeitstempel vorhanden).
        holding_days: Haltedauer in Tagen (0.0, falls unbekannt).
        entry_time: Zeitpunkt des Einstiegs.
        exit_time: Zeitpunkt des Ausstiegs.
        close_reason: Grund des Ausstiegs (Textlabel).
        outcome: ``"win"``/``"loss"``/``"breakeven"``.
        labels: Zusätzliche Dimensions-Labels (z. B. ``pattern``, ``market_phase``)
            aus der Metadata des Quell-Trades; leer, wenn nicht vorhanden.
        reasons: Begründungen der Empfehlung (Transparenz).
        warnings: Warnungen der Empfehlung.
        metadata: Zusatzinformationen des Quell-Trades.
    """

    source: str
    trade_id: str
    symbol: str
    recommendation_id: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    strategy: str
    risk_level: str
    pnl: float
    pnl_pct: float
    return_on_risk: float
    risk_reward: float
    holding_days: float
    outcome: str
    score: float | None = None
    holding_time: timedelta | None = None
    entry_time: datetime | None = None
    exit_time: datetime | None = None
    close_reason: str = ""
    labels: dict[str, str] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_win(self) -> bool:
        """Ob der Trade ein Gewinn ist."""
        return self.outcome == "win"

    @property
    def is_loss(self) -> bool:
        """Ob der Trade ein Verlust ist."""
        return self.outcome == "loss"


@dataclass(frozen=True, slots=True)
class GroupStatistics:
    """Kennzahlen einer Trade-Gruppe (unveränderlich, reproduzierbar).

    Attributes:
        label: Name der Gruppe (z. B. ``"long"``, ``"trend_following"``, ``"low"``).
        trade_count: Anzahl Trades in der Gruppe.
        win_rate: Trefferquote 0..1.
        loss_rate: Verlustquote 0..1.
        profit_factor: Bruttogewinn / Bruttoverlust (``inf`` ohne Verluste).
        average_winner: Durchschnittlicher Gewinn (≥ 0).
        average_loser: Durchschnittlicher Verlust (≤ 0).
        average_return: Durchschnittliches Ergebnis je Trade (Kontowährung).
        average_holding_time: Durchschnittliche Haltedauer in Tagen.
        maximum_drawdown: Maximaler Drawdown der Gruppen-Kapitalkurve (Prozent).
        total_pnl: Summe der Ergebnisse (Kontowährung).
    """

    label: str
    trade_count: int = 0
    win_rate: float = 0.0
    loss_rate: float = 0.0
    profit_factor: float = 0.0
    average_winner: float = 0.0
    average_loser: float = 0.0
    average_return: float = 0.0
    average_holding_time: float = 0.0
    maximum_drawdown: float = 0.0
    total_pnl: float = 0.0


@dataclass(frozen=True, slots=True)
class AnalyticsModelOutput:
    """Ergebnis eines einzelnen Analysemodells (unveränderlich).

    Attributes:
        name: Name des Modells.
        metrics: Skalare Kennzahlen (Name -> Wert).
        statistics: Gruppierte Kennzahlen (Name -> :class:`GroupStatistics`
            bzw. verschachtelte Struktur).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Während der Berechnung gesammelte Warnungen.
        details: Zusätzliche, nicht rein numerische Aufschlüsselung.
    """

    name: str
    metrics: dict[str, float] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalyticsContext:
    """Eingabe für ein Analysemodell (unveränderlich).

    Die Engine normalisiert die Trades und stellt Journal, Konfiguration und
    Rahmenwerte **vorab** bereit, sodass jedes Modell unabhängig darauf zugreift.

    Attributes:
        trades: Alle normalisierten Trades (Backtest + Paper Trading).
        journal: Journal-Einträge aus dem Paper-Trading-Report (nur Lesen).
        backtest_id: Bezeichner des Backtest-Reports (oder leer).
        paper_trading_id: Bezeichner des Paper-Trading-Reports (oder leer).
        symbol: Analysiertes Symbol/Label.
        timeframe: Zeitebenen-Label.
        config: Bucket-/Schwellen-Konfiguration (aus ``analytics_rules.toml``).
        metadata: Zusatzinformationen.
    """

    trades: Sequence[AnalyticsTrade]
    journal: Sequence[JournalEntry] = ()
    backtest_id: str = ""
    paper_trading_id: str = ""
    symbol: str = ""
    timeframe: str = "base"
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def long_trades(self) -> list[AnalyticsTrade]:
        """Alle LONG-Trades."""
        return [t for t in self.trades if t.direction is Direction.LONG]

    @property
    def short_trades(self) -> list[AnalyticsTrade]:
        """Alle SHORT-Trades."""
        return [t for t in self.trades if t.direction is Direction.SHORT]


@dataclass(frozen=True, slots=True)
class AnalyticsResult:
    """Gebündeltes Analyseergebnis (unveränderlich).

    Enthält die aggregierten Kennzahlen und alle gruppierten Statistiken, sodass
    ein späteres Dashboard sie **ohne weitere Berechnung** direkt anzeigen kann.

    Attributes:
        analytics_id: Stabiler Bezeichner der Analyse.
        backtest_id: Bezeichner des ausgewerteten Backtest-Reports.
        paper_trading_id: Bezeichner des ausgewerteten Paper-Trading-Reports.
        trade_count: Anzahl ausgewerteter Trades.
        win_rate: Trefferquote 0..1.
        loss_rate: Verlustquote 0..1.
        profit_factor: Bruttogewinn / Bruttoverlust.
        expectancy: Erwartungswert je Trade (Kontowährung).
        average_winner: Durchschnittlicher Gewinn.
        average_loser: Durchschnittlicher Verlust.
        maximum_drawdown: Maximaler Drawdown (Prozent).
        average_holding_time: Durchschnittliche Haltedauer (Tage).
        average_risk_reward: Durchschnittliches Chance-Risiko-Verhältnis.
        long_statistics: Kennzahlen der LONG-Trades.
        short_statistics: Kennzahlen der SHORT-Trades.
        strategy_statistics: Kennzahlen je Strategie.
        pattern_statistics: Kennzahlen je Pattern-Label.
        recommendation_statistics: Kennzahlen je Recommendation Strength.
        risk_statistics: Kennzahlen je Risiko-Level.
        market_statistics: Kennzahlen je Marktphasen-Label.
        time_statistics: Zeitliche Kennzahlen (Wochentag/Monat/Stunde/Haltedauer).
        journal_statistics: Kennzahlen aus dem Journal.
        performance: Aggregierte Performance-Kennzahlen (Rendite, Drawdown, …).
        summary: Menschenlesbare Zusammenfassung.
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen (u. a. Modell-Kennzahlen).
        timestamp: Zeitpunkt der Analyse.
    """

    analytics_id: str
    backtest_id: str
    paper_trading_id: str
    trade_count: int
    win_rate: float
    loss_rate: float
    profit_factor: float
    expectancy: float
    average_winner: float
    average_loser: float
    maximum_drawdown: float
    average_holding_time: float
    average_risk_reward: float
    long_statistics: GroupStatistics
    short_statistics: GroupStatistics
    strategy_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    pattern_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    recommendation_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    risk_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    market_statistics: dict[str, GroupStatistics] = field(default_factory=dict)
    time_statistics: dict[str, dict[str, GroupStatistics]] = field(default_factory=dict)
    journal_statistics: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, float] = field(default_factory=dict)
    summary: str = ""
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class AnalyticsReport:
    """Lauf-Report des Analytics-Frameworks (unveränderlich).

    Attributes:
        result: Das gebündelte Analyseergebnis.
        model_outputs: Ausgaben der einzelnen Analysemodelle (Name -> Output).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen.
    """

    result: AnalyticsResult
    model_outputs: dict[str, AnalyticsModelOutput] = field(default_factory=dict)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def trade_count(self) -> int:
        """Anzahl ausgewerteter Trades."""
        return self.result.trade_count
