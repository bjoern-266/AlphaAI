"""Domänenmodell: Risiko-Ergebnisse.

Enthält die unveränderlichen Datentypen der Risk Engine: die Risikostufe
:class:`RiskLevel`, eine offene Position :class:`OpenPosition` (vorbereitet für
Portfolio-Risiko), die Einzelkomponente :class:`RiskComponent`, die
Modellausgabe :class:`RiskModelOutput`, die Positionsgrößen-Berechnung
:class:`PositionSizing`, den Eingabe-Kontext :class:`RiskContext`, die
Einzelbewertung :class:`RiskResult` und den Lauf-Report :class:`RiskReport`.

Teil der Entities-Schicht (``models/``). Abhängigkeiten zeigen nur auf andere
Modelle und auf ``core`` (Konfiguration) – **kein** Import aus ``engines`` o. Ä.
Die Berechnungs-*Logik* (Komponenten, Positionsgröße) liegt in ``risk.base``.

Die Risk Engine liefert ausschließlich diese Ergebnisse. Sie trifft **keine**
Kauf-/Verkaufsentscheidung, eröffnet **keine** Position und sendet **keine**
Orders.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd

from core.config import AccountConfig, RiskConfig
from models.indicator import IndicatorResult
from models.score import ScoreResult

# Die zehn Risikokomponenten, die jede Bewertung getrennt speichert.
# ``news`` ist vorbereitet (neutral), bis eine Nachrichtenquelle angebunden ist.
RISK_COMPONENT_NAMES: tuple[str, ...] = (
    "volatility",
    "liquidity",
    "gap",
    "spread",
    "atr",
    "market",
    "correlation",
    "portfolio_exposure",
    "data_quality",
    "news",
)


class RiskLevel(Enum):
    """Grobe Risikostufe einer Bewertung."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass(frozen=True, slots=True)
class OpenPosition:
    """Eine bereits offene Position (vorbereitet für Portfolio-Risiko).

    Attributes:
        symbol: Symbol der offenen Position.
        value: Aktueller Marktwert in Kontowährung.
        direction: ``"long"`` oder ``"short"``.
        correlation_group: Optionale Gruppe (z. B. Sektor/Index) zur
            groben Korrelationsschätzung.
    """

    symbol: str
    value: float
    direction: str = "long"
    correlation_group: str = ""


@dataclass(frozen=True, slots=True)
class RiskComponent:
    """Eine einzelne Risikokomponente (unveränderlich).

    Attributes:
        name: Komponentenname (aus :data:`RISK_COMPONENT_NAMES`).
        value: Risikowert 0..100 (höher = riskanter).
        reason: Erklärung des Werts (Transparenz).
    """

    name: str
    value: float
    reason: str


@dataclass(frozen=True, slots=True)
class RiskModelOutput:
    """Ergebnis eines einzelnen Risk-Modells (unveränderlich).

    Attributes:
        name: Name des Risk-Modells.
        value: Risikowert des Modells (0..100; höher = riskanter).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Während der Berechnung gesammelte Warnungen.
        details: Zusätzliche Aufschlüsselung (z. B. Positionsgrößen-Zahlen).
    """

    name: str
    value: float
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class PositionSizing:
    """Ergebnis der Positionsgrößen-Berechnung (unveränderlich).

    Alle Preis-/Wertangaben sind in Kontowährung; Abstände sind Preisabstände.

    Attributes:
        suggested_position_size: Empfohlener Positionswert (Kontowährung).
        maximum_risk_pct: Maximales Risiko je Trade in Prozent.
        maximum_portfolio_exposure: Maximales Gesamtengagement (Kontowährung).
        estimated_shares: Geschätzte Stückzahl (ganzzahlig ohne Bruchstücke).
        estimated_order_value: Geschätzter Orderwert (Stück × Preis).
        estimated_slippage: Geschätzte Slippage (Kontowährung).
        estimated_commission: Geschätzte Kommission (Kontowährung).
        suggested_stop_distance: Empfohlener Stop-Abstand (Preisabstand).
        suggested_take_profit: Empfohlener Take-Profit-Abstand (Preisabstand).
        suggested_risk_reward: Empfohlenes Chance-Risiko-Verhältnis.
    """

    suggested_position_size: float = 0.0
    maximum_risk_pct: float = 0.0
    maximum_portfolio_exposure: float = 0.0
    estimated_shares: float = 0.0
    estimated_order_value: float = 0.0
    estimated_slippage: float = 0.0
    estimated_commission: float = 0.0
    suggested_stop_distance: float = 0.0
    suggested_take_profit: float = 0.0
    suggested_risk_reward: float = 0.0


@dataclass(frozen=True, slots=True)
class RiskContext:
    """Eingabe für ein Risk-Modell (unveränderlich).

    Attributes:
        score_result: Die bewertete Hypothese (Score der Score Engine).
        indicators: Ergebnis der Indicator Engine (u. a. ATR, rel. Volumen).
        account: Depot-/Broker-Angaben (aus ``settings.toml``).
        risk: Risikoparameter (aus ``settings.toml``).
        data: Optionale OHLCV-Rohdaten (Preis, Volumen, Gaps).
        open_positions: Bereits offene Positionen (Portfolio-Vorbereitung).
        symbol: Symbolname.
        timeframe: Zeitebenen-Label.
    """

    score_result: ScoreResult
    indicators: IndicatorResult
    account: AccountConfig
    risk: RiskConfig
    data: pd.DataFrame | None = None
    open_positions: Sequence[OpenPosition] = ()
    symbol: str = ""
    timeframe: str = "base"

    @property
    def entry_price(self) -> float | None:
        """Letzter Schlusskurs (angenommener Einstieg) oder ``None``."""
        if self.data is None or self.data.empty or "close" not in self.data.columns:
            return None
        price = float(self.data["close"].iloc[-1])
        return price if price > 0 else None

    @property
    def atr(self) -> float | None:
        """Letzter ATR(14) aus den Indikatoren oder ``None``."""
        return self.indicators.atr14


@dataclass(frozen=True, slots=True)
class RiskResult:
    """Objektive Risikobewertung einer Hypothese (unveränderlich).

    Attributes:
        risk_id: Stabiler Bezeichner der Risikobewertung.
        score_id: Bezeichner der zugrunde liegenden Score-Bewertung.
        hypothesis_id: Bezeichner der bewerteten Hypothese.
        overall_risk: Gesamtrisiko 0..100 (höher = riskanter).
        risk_level: Grobe Stufe (LOW/MEDIUM/HIGH).
        suggested_position_size: Empfohlener Positionswert (Kontowährung).
        maximum_risk_pct: Maximales Risiko je Trade in Prozent.
        maximum_portfolio_exposure: Maximales Gesamtengagement (Kontowährung).
        estimated_shares: Geschätzte Stückzahl.
        estimated_order_value: Geschätzter Orderwert.
        estimated_slippage: Geschätzte Slippage.
        estimated_commission: Geschätzte Kommission.
        suggested_stop_distance: Empfohlener Stop-Abstand (Preisabstand).
        suggested_take_profit: Empfohlener Take-Profit-Abstand (Preisabstand).
        suggested_risk_reward: Empfohlenes Chance-Risiko-Verhältnis.
        risk_components: Alle zehn Komponenten (Name -> Wert 0..100).
        reasons: Nachvollziehbare Begründungen (Transparenz).
        warnings: Gesammelte Warnungen.
        metadata: Zusatzinformationen (u. a. alle Modell-Werte).
        timestamp: Zeitpunkt der Bewertung.
    """

    risk_id: str
    score_id: str
    hypothesis_id: str
    overall_risk: float
    risk_level: RiskLevel
    suggested_position_size: float
    maximum_risk_pct: float
    maximum_portfolio_exposure: float
    estimated_shares: float
    estimated_order_value: float
    estimated_slippage: float
    estimated_commission: float
    suggested_stop_distance: float
    suggested_take_profit: float
    suggested_risk_reward: float
    risk_components: dict[str, float] = field(default_factory=dict)
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime | None = None


@dataclass(frozen=True, slots=True)
class RiskReport:
    """Gesamtergebnis eines Risk-Laufs für ein Symbol (unveränderlich).

    Attributes:
        results: Alle Risikobewertungen (eine je Hypothese/Score).
        calculation_time: Reine Rechenzeit in Sekunden.
        valid: Ob das Ergebnis grundsätzlich verwertbar ist.
        warnings: Gesammelte Warnungen (z. B. fehlende Scores).
        metadata: Zusatzinformationen (Symbol, Timeframe, …).
    """

    results: list[RiskResult] = field(default_factory=list)
    calculation_time: float = 0.0
    valid: bool = True
    warnings: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def by_score(self, score_id: str) -> list[RiskResult]:
        """Gibt alle Bewertungen zu einer Score-ID zurück."""
        return [r for r in self.results if r.score_id == score_id]

    def by_level(self, level: RiskLevel) -> list[RiskResult]:
        """Gibt alle Bewertungen einer Risikostufe zurück."""
        return [r for r in self.results if r.risk_level is level]

    def highest_risk(self, limit: int = 1) -> list[RiskResult]:
        """Gibt die Bewertungen mit dem höchsten Gesamtrisiko zurück.

        Reine Sortierung/Anzeige – **keine** Handelsempfehlung.
        """
        return sorted(self.results, key=lambda r: r.overall_risk, reverse=True)[:limit]

    @property
    def risk_count(self) -> int:
        """Anzahl erzeugter Risikobewertungen."""
        return len(self.results)
