"""Domänenmodell: Historisches Backtesting.

Enthält die unveränderlichen Datentypen des Backtesting-Frameworks. Das
Framework **bewertet ausschließlich**, wie sich die bestehenden AlphaAI-
Empfehlungen historisch entwickelt hätten – es erzeugt **keine** neuen
Handelsregeln, verändert **keine** Empfehlung, führt **keine** echte Order aus
und simuliert Trades ausschließlich rechnerisch.

Enthaltene Typen:

* :class:`TradeOutcome` / :class:`ExitReason` – Ausgang und Grund eines Trades,
* :class:`HistoricalSignal` – ein vom Historical Runner erzeugtes Einstiegs-
  Signal (eine bestehende Empfehlung an einem historischen Zeitpunkt),
* :class:`SimulatedTrade` – ein vollständig nachvollziehbarer simulierter Trade,
* :class:`EquityPoint` – ein Punkt der Kapitalkurve,
* :class:`BenchmarkResult` – Vergleichsergebnis (z. B. Buy & Hold),
* :class:`BacktestModelOutput` – Ausgabe eines einzelnen Backtest-Modells,
* :class:`BacktestContext` – Eingabe für die Backtest-Modelle,
* :class:`BacktestResult` – das Gesamtergebnis eines Backtests,
* :class:`BacktestReport` – der Lauf-Report über mehrere Symbole.

Teil der Entities-Schicht (``models/``). Die Abhängigkeiten zeigen ausschließlich
auf andere Modelle (:mod:`models.recommendation`) – **kein** Import aus
``engines``, ``backtesting`` o. Ä. Die Berechnungs-*Logik* liegt in den Modulen
des Pakets ``backtesting`` (Kennzahlen, Kapitalkurve, Statistik, Benchmark,
Trade-Simulator, Historical Runner).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from models.recommendation import Direction, RecommendationStrength, SuggestedAction

# Die drei risikoadjustierten Kennzahlen. Sie sind **vorbereitet**: die
# Formeln sind implementiert, aber bewusst nicht annualisiert/kalibriert, bis
# ein realer Datensatz und eine Referenz-Periodizität feststehen.
PREPARED_RATIO_NAMES: tuple[str, ...] = ("sharpe", "sortino", "calmar")


class TradeOutcome(Enum):
    """Ausgang eines simulierten Trades."""

    WIN = "win"
    LOSS = "loss"
    BREAKEVEN = "breakeven"


class ExitReason(Enum):
    """Grund für den Ausstieg aus einem simulierten Trade."""

    STOP = "stop"
    TAKE_PROFIT = "take_profit"
    TIME = "time"
    END_OF_DATA = "end_of_data"


@dataclass(frozen=True, slots=True)
class HistoricalSignal:
    """Ein historisches Einstiegs-Signal (unveränderlich).

    Ein Signal ist eine **bestehende** Empfehlung, ausgewertet an einem
    historischen Zeitpunkt. Es enthält alle Größen, die der Trade-Simulator
    benötigt – sämtlich aus der bestehenden Pipeline abgeleitet, ohne neue
    Handelsregel.

    Attributes:
        bar_index: Position der Kerze im historischen DataFrame.
        timestamp: Zeitstempel der Signal-Kerze.
        entry_price: Angenommener Einstieg (Schlusskurs der Signal-Kerze).
        direction: Handelsrichtung der Empfehlung (LONG/SHORT/NEUTRAL).
        recommendation_strength: Stärke der Empfehlung (VERY_HIGH … REJECT).
        suggested_action: Vorgeschlagene Handlung (OPEN/WAIT/MONITOR/SKIP).
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        stop_distance: Empfohlener Stop-Abstand (Preisabstand, aus der Risk Engine).
        take_profit_distance: Empfohlener Take-Profit-Abstand (Preisabstand).
        shares: Empfohlene Stückzahl (aus der Positionsgröße, settings.toml).
        risk_amount: Riskierter Betrag in Kontowährung (Stück × Stop-Abstand).
        risk_reward: Geplantes Chance-Risiko-Verhältnis.
        commission: Geschätzte Kommission (Kontowährung).
        slippage: Geschätzte Slippage (Kontowährung).
        reasons: Begründungen der Empfehlung (Transparenz).
        warnings: Warnungen der Empfehlung.
    """

    bar_index: int
    timestamp: datetime | None
    entry_price: float
    direction: Direction
    recommendation_strength: RecommendationStrength
    suggested_action: SuggestedAction
    recommendation_id: str
    stop_distance: float
    take_profit_distance: float
    shares: float
    risk_amount: float
    risk_reward: float
    commission: float = 0.0
    slippage: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_actionable(self) -> bool:
        """Ob aus dem Signal überhaupt ein Trade werden kann.

        Actionable ist ein Signal nur, wenn es eine klare Richtung, eine
        vorgeschlagene Eröffnung (``OPEN``), eine positive Stückzahl und einen
        positiven Stop-Abstand besitzt.
        """
        return (
            self.direction is not Direction.NEUTRAL
            and self.suggested_action is SuggestedAction.OPEN
            and self.shares > 0
            and self.stop_distance > 0
        )


@dataclass(frozen=True, slots=True)
class SimulatedTrade:
    """Ein vollständig nachvollziehbarer simulierter Trade (unveränderlich).

    Es wird **keine** echte Order ausgeführt. Für jeden Trade werden Einstieg,
    Ausstieg, Stop, Take-Profit, Risiko und die zugrunde liegende Empfehlung
    (Richtung, Stärke, Begründungen) gespeichert.

    Attributes:
        trade_id: Stabiler Bezeichner des Trades.
        symbol: Gehandeltes Symbol.
        direction: Handelsrichtung (LONG/SHORT).
        recommendation_strength: Stärke der zugrunde liegenden Empfehlung.
        recommendation_id: Bezeichner der zugrunde liegenden Empfehlung.
        entry_time: Zeitpunkt des Einstiegs.
        entry_price: Einstiegspreis.
        exit_time: Zeitpunkt des Ausstiegs.
        exit_price: Ausstiegspreis.
        stop_price: Stop-Loss-Preis.
        take_profit_price: Take-Profit-Preis.
        shares: Gehandelte Stückzahl (Fractional Shares möglich).
        risk_amount: Riskierter Betrag in Kontowährung.
        position_value: Positionswert bei Einstieg (Stück × Einstiegspreis).
        profit: Netto-Ergebnis in Kontowährung (nach Kosten).
        profit_pct: Ergebnis relativ zum Positionswert (Prozent).
        return_on_risk: Ergebnis als R-Vielfaches (profit / risk_amount).
        risk_reward: Geplantes Chance-Risiko-Verhältnis.
        holding_bars: Haltedauer in Kerzen.
        holding_time: Haltedauer als Zeitspanne (falls Zeitstempel vorhanden).
        outcome: Ausgang (WIN/LOSS/BREAKEVEN).
        exit_reason: Grund des Ausstiegs (STOP/TAKE_PROFIT/TIME/END_OF_DATA).
        commission: Angesetzte Kommission (Kontowährung).
        slippage: Angesetzte Slippage (Kontowährung).
        reasons: Begründungen der Empfehlung (Transparenz).
        warnings: Warnungen der Empfehlung.
        metadata: Zusatzinformationen.
    """

    trade_id: str
    symbol: str
    direction: Direction
    recommendation_strength: RecommendationStrength
    recommendation_id: str
    entry_time: datetime | None
    entry_price: float
    exit_time: datetime | None
    exit_price: float
    stop_price: float
    take_profit_price: float
    shares: float
    risk_amount: float
    position_value: float
    profit: float
    profit_pct: float
    return_on_risk: float
    risk_reward: float
    holding_bars: int
    holding_time: timedelta | None
    outcome: TradeOutcome
    exit_reason: ExitReason
    commission: float = 0.0
    slippage: float = 0.0
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_win(self) -> bool:
        """Ob der Trade ein Gewinn ist."""
        return self.outcome is TradeOutcome.WIN

    @property
    def is_loss(self) -> bool:
        """Ob der Trade ein Verlust ist."""
        return self.outcome is TradeOutcome.LOSS


@dataclass(frozen=True, slots=True)
class EquityPoint:
    """Ein Punkt der Kapitalkurve (unveränderlich).

    Attributes:
        timestamp: Zeitpunkt des Punkts (Ausstieg des jeweiligen Trades).
        equity: Kontostand nach dem Trade (Kontowährung).
        drawdown: Absoluter Rückgang vom bisherigen Hoch (Kontowährung).
        drawdown_pct: Rückgang vom bisherigen Hoch in Prozent (0..100).
    """

    timestamp: datetime | None
    equity: float
    drawdown: float
    drawdown_pct: float


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Ergebnis eines Vergleichsmaßstabs, z. B. Buy & Hold (unveränderlich).

    Attributes:
        name: Name der Referenz (z. B. ``"buy_and_hold"``).
        start_price: Preis zu Beginn des Zeitraums.
        end_price: Preis am Ende des Zeitraums.
        start_equity: Startkapital (Kontowährung).
        end_equity: Endkapital der Referenz (Kontowährung).
        return_pct: Rendite der Referenz in Prozent.
        reasons: Nachvollziehbare Begründungen (Transparenz).
    """

    name: str
    start_price: float
    end_price: float
    start_equity: float
    end_equity: float
    return_pct: float
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class BacktestModelOutput:
    """Ergebnis eines einzelnen Backtest-Modells (unveränderlich).

    Attributes:
        name: Name des Modells.
        metrics: Berechnete numerische Kennzahlen (Name -> Wert).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Während der Berechnung gesammelte Warnungen.
        details: Zusätzliche, nicht rein numerische Aufschlüsselung
            (z. B. vorbereitete Kennzahlen als ``float | None`` oder ein
            :class:`BenchmarkResult`).
    """

    name: str
    metrics: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class BacktestContext:
    """Eingabe für ein Backtest-Modell (unveränderlich).

    Die Engine ermittelt Trades, Kapitalkurve und Benchmark **vorab** (analog
    zum RecommendationContext) und stellt sie hier bereit, sodass jedes Modell
    unabhängig darauf zugreift.

    Attributes:
        symbol: Analysiertes Symbol.
        timeframe: Zeitebenen-Label.
        start_date: Beginn des Auswertungszeitraums.
        end_date: Ende des Auswertungszeitraums.
        starting_capital: Startkapital (aus ``settings.toml``).
        trades: Alle simulierten Trades.
        equity_curve: Die Kapitalkurve.
        signal_count: Anzahl actionabler Signale (Einstiegskandidaten).
        benchmark: Optionaler Vergleichsmaßstab (z. B. Buy & Hold).
        metadata: Zusatzinformationen.
    """

    symbol: str
    timeframe: str
    starting_capital: float
    trades: Sequence[SimulatedTrade]
    equity_curve: Sequence[EquityPoint]
    signal_count: int = 0
    start_date: datetime | None = None
    end_date: datetime | None = None
    benchmark: BenchmarkResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def trade_count(self) -> int:
        """Anzahl simulierter Trades."""
        return len(self.trades)


@dataclass(frozen=True, slots=True)
class BacktestResult:
    """Gesamtergebnis eines Backtests für **ein** Symbol (unveränderlich).

    Bewertet objektiv, wie sich die bestehenden Empfehlungen historisch
    entwickelt hätten. Enthält **keine** neue Handelsregel.

    Attributes:
        backtest_id: Stabiler Bezeichner des Backtests.
        symbol: Analysiertes Symbol.
        timeframe: Zeitebenen-Label.
        start_date: Beginn des Auswertungszeitraums.
        end_date: Ende des Auswertungszeitraums.
        signal_count: Anzahl actionabler Signale (Einstiegskandidaten).
        trade_count: Anzahl simulierter Trades.
        win_rate: Trefferquote 0..1.
        loss_rate: Verlustquote 0..1.
        profit_factor: Bruttogewinn / Bruttoverlust (``inf`` ohne Verluste).
        average_win: Durchschnittlicher Gewinn (Kontowährung, ≥ 0).
        average_loss: Durchschnittlicher Verlust (Kontowährung, ≤ 0).
        average_risk_reward: Durchschnittliches geplantes Chance-Risiko-Verhältnis.
        average_holding_time: Durchschnittliche Haltedauer in Kerzen.
        maximum_drawdown: Maximaler Rückgang der Kapitalkurve in Prozent (0..100).
        expectancy: Erwartungswert je Trade (Kontowährung).
        sharpe_ratio: Sharpe-Ratio (**vorbereitet**; ``None`` bei zu wenig Daten).
        sortino_ratio: Sortino-Ratio (**vorbereitet**; ``None`` bei zu wenig Daten).
        calmar_ratio: Calmar-Ratio (**vorbereitet**; ``None`` bei zu wenig Daten).
        total_return: Gesamt-Netto-Ergebnis (Kontowährung).
        total_return_pct: Gesamtrendite in Prozent (relativ zum Startkapital).
        final_equity: Endkapital (Kontowährung).
        equity_curve: Die Kapitalkurve.
        trades: Alle simulierten Trades (vollständig nachvollziehbar).
        benchmark: Optionaler Vergleichsmaßstab (z. B. Buy & Hold).
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        summary: Menschenlesbare Kurzfassung.
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen (u. a. Modellkennzahlen).
        timestamp: Zeitpunkt des Backtests.
    """

    backtest_id: str
    symbol: str
    timeframe: str
    start_date: datetime | None
    end_date: datetime | None
    signal_count: int
    trade_count: int
    win_rate: float
    loss_rate: float
    profit_factor: float
    average_win: float
    average_loss: float
    average_risk_reward: float
    average_holding_time: float
    maximum_drawdown: float
    expectancy: float
    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    total_return: float
    total_return_pct: float
    final_equity: float
    equity_curve: list[EquityPoint] = field(default_factory=list)
    trades: list[SimulatedTrade] = field(default_factory=list)
    benchmark: BenchmarkResult | None = None
    valid: bool = True
    summary: str = ""
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None

    @property
    def outperformed_benchmark(self) -> bool | None:
        """Ob AlphaAI die Referenz übertroffen hat (``None`` ohne Referenz).

        Reiner Vergleich/Anzeige – **keine** Handelsentscheidung.
        """
        if self.benchmark is None:
            return None
        return self.total_return_pct > self.benchmark.return_pct


@dataclass(frozen=True, slots=True)
class BacktestReport:
    """Gesamtergebnis eines Backtest-Laufs über ein oder mehrere Symbole.

    Attributes:
        results: Alle Backtest-Ergebnisse (eines je Symbol).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen (z. B. fehlende Daten).
        metadata: Zusatzinformationen.
    """

    results: list[BacktestResult] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_symbol(self, symbol: str) -> list[BacktestResult]:
        """Gibt alle Ergebnisse eines Symbols zurück."""
        target = symbol.strip().upper()
        return [r for r in self.results if r.symbol.strip().upper() == target]

    def best(self, limit: int = 1) -> list[BacktestResult]:
        """Gibt die Ergebnisse mit der höchsten Gesamtrendite zurück.

        Reine Sortierung/Anzeige – **keine** Handelsentscheidung.
        """
        return sorted(self.results, key=lambda r: r.total_return_pct, reverse=True)[:limit]

    @property
    def backtest_count(self) -> int:
        """Anzahl durchgeführter Backtests."""
        return len(self.results)
