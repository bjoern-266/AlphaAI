"""Das simulierte Paper-Portfolio.

Der :class:`PaperPortfolio` speichert **ausschließlich simulierte** Positionen –
**keine** Broker-API, **keine** echten Orders. Es verwaltet offene und
geschlossene Positionen, den Kontostand (Kapital + realisierte + unrealisierte
Ergebnisse), das Exposure und den Drawdown. Fractional Shares werden vollständig
unterstützt.

Validierung beim Eröffnen (wirft :class:`PaperTradingValidationError`):

* keine **doppelte** Position derselben Empfehlung (solange offen),
* keine **negative** Positionsgröße (Stückzahl/Wert > 0),
* keine **ungültigen** Preise (Einstieg > 0, Stop/Take-Profit ≥ 0),
* keine **ungültigen** Zeitstempel,
* keine **ungültigen** Statuswechsel (über :mod:`paper_trading.order`).

Die einzelnen Positionen sind unveränderlich; das Portfolio schreibt sie über die
Funktionen aus :mod:`paper_trading.position` fort.
"""

from __future__ import annotations

from datetime import datetime

from core.exceptions import PaperTradingValidationError
from models.paper_trading import (
    CloseReason,
    OrderAction,
    PaperEquityPoint,
    PaperOrder,
    PaperPosition,
)
from models.recommendation import Direction, RecommendationStrength
from paper_trading import order as order_mod
from paper_trading import position as position_mod
from paper_trading.journal import PaperJournal


class PaperPortfolio:
    """Verwaltet die simulierten Positionen und Kennzahlen eines Symbols.

    Args:
        starting_capital: Startkapital in Kontowährung (> 0).
        fractional_shares: Ob Bruchstücke erlaubt sind (aus ``settings.toml``).
    """

    def __init__(self, starting_capital: float, fractional_shares: bool = True) -> None:
        if starting_capital <= 0:
            raise PaperTradingValidationError("Startkapital muss größer als 0 sein.")
        self._starting_capital = float(starting_capital)
        self._fractional_shares = bool(fractional_shares)
        self._positions: dict[str, PaperPosition] = {}
        self._context: dict[str, dict[str, float]] = {}
        self._orders: list[PaperOrder] = []
        self._equity_curve: list[PaperEquityPoint] = []
        self._journal = PaperJournal()
        self._realized_pnl = 0.0
        self._peak_equity = float(starting_capital)
        self._max_drawdown_pct = 0.0
        self._seq = 0

    # ------------------------------------------------------------------ #
    # Eigenschaften / Kennzahlen
    # ------------------------------------------------------------------ #

    @property
    def starting_capital(self) -> float:
        """Startkapital."""
        return self._starting_capital

    @property
    def fractional_shares(self) -> bool:
        """Ob Bruchstücke erlaubt sind."""
        return self._fractional_shares

    @property
    def journal(self) -> PaperJournal:
        """Das automatische Journal."""
        return self._journal

    @property
    def orders(self) -> list[PaperOrder]:
        """Alle simulierten Orders (Audit)."""
        return list(self._orders)

    @property
    def equity_curve(self) -> list[PaperEquityPoint]:
        """Die Kapitalkurve."""
        return list(self._equity_curve)

    @property
    def realized_pnl(self) -> float:
        """Summe realisierter Ergebnisse."""
        return self._realized_pnl

    @property
    def maximum_drawdown_pct(self) -> float:
        """Maximaler Drawdown in Prozent (0..100)."""
        return self._max_drawdown_pct

    def positions(self) -> list[PaperPosition]:
        """Alle Positionen (offen und geschlossen), in Einfüge-Reihenfolge."""
        return list(self._positions.values())

    def open_positions(self) -> list[PaperPosition]:
        """Alle offenen Positionen."""
        return [p for p in self._positions.values() if p.is_open]

    def unrealized_pnl(self) -> float:
        """Summe unrealisierter Ergebnisse (offene Positionen)."""
        return sum(p.pnl for p in self.open_positions())

    def equity(self) -> float:
        """Aktueller Kontostand = Startkapital + realisiert + unrealisiert."""
        return self._starting_capital + self._realized_pnl + self.unrealized_pnl()

    def exposure_pct(self) -> float:
        """Aktuelles Exposure (Marktwert offener Positionen / Kapital, Prozent)."""
        equity = self.equity()
        if equity <= 0:
            return 0.0
        return sum(abs(p.market_value) for p in self.open_positions()) / equity * 100.0

    def running_drawdown_pct(self) -> float:
        """Aktueller Drawdown vom bisherigen Kapital-Hoch (Prozent)."""
        equity = self.equity()
        if self._peak_equity <= 0:
            return 0.0
        return max(0.0, (self._peak_equity - equity) / self._peak_equity * 100.0)

    def context_for(self, position_id: str) -> dict[str, float]:
        """Gibt die Portfolio-Kennzahlen zur letzten Bewertung einer Position zurück."""
        return self._context.get(
            position_id,
            {
                "current_equity": self.equity(),
                "portfolio_exposure": self.exposure_pct(),
                "running_drawdown": self.running_drawdown_pct(),
                "maximum_drawdown": self._max_drawdown_pct,
            },
        )

    # ------------------------------------------------------------------ #
    # Order-/Positions-Management
    # ------------------------------------------------------------------ #

    def has_open_for_recommendation(self, recommendation_id: str) -> bool:
        """Ob bereits eine **offene** Position zu dieser Empfehlung existiert."""
        return any(
            p.recommendation_id == recommendation_id and p.is_open for p in self._positions.values()
        )

    def open_position(
        self,
        recommendation_id: str,
        symbol: str,
        direction: Direction,
        recommendation_strength: RecommendationStrength,
        entry_price: float,
        stop_price: float,
        take_profit_price: float,
        shares: float,
        risk_amount: float,
        entry_time: datetime | None,
        reasons: list[str] | None = None,
        warnings: list[str] | None = None,
        metadata: dict | None = None,
    ) -> PaperPosition:
        """Eröffnet eine simulierte Position (mit vollständiger Validierung)."""
        self._validate_open(
            recommendation_id, entry_price, stop_price, take_profit_price, shares, entry_time
        )
        self._seq += 1
        position_id = f"pos:{symbol}:{self._seq}"
        shares_final = shares if self._fractional_shares else float(int(shares))
        if shares_final <= 0:
            raise PaperTradingValidationError("Positionsgröße nach Rundung nicht positiv.")
        position = position_mod.open_position(
            position_id=position_id,
            recommendation_id=recommendation_id,
            symbol=symbol,
            direction=direction,
            recommendation_strength=recommendation_strength,
            entry_price=entry_price,
            stop_price=stop_price,
            take_profit_price=take_profit_price,
            shares=shares_final,
            risk_amount=risk_amount,
            entry_time=entry_time,
            reasons=reasons,
            warnings=warnings,
            metadata=metadata,
        )
        self._positions[position_id] = position
        self._record_order(position, OrderAction.OPEN, entry_price, entry_time, "Eröffnung")
        self._journal.record_open(position, entry_time)
        self._stamp_context(position_id)
        return position

    def _validate_open(
        self,
        recommendation_id: str,
        entry_price: float,
        stop_price: float,
        take_profit_price: float,
        shares: float,
        entry_time: datetime | None,
    ) -> None:
        """Prüft die Bedingungen für eine Eröffnung."""
        if self.has_open_for_recommendation(recommendation_id):
            raise PaperTradingValidationError(
                f"Doppelte Position für Empfehlung '{recommendation_id}' ist nicht erlaubt."
            )
        if shares <= 0:
            raise PaperTradingValidationError("Positionsgröße (Stückzahl) muss positiv sein.")
        if entry_price <= 0:
            raise PaperTradingValidationError("Ungültiger Einstiegspreis (≤ 0).")
        if stop_price < 0 or take_profit_price < 0:
            raise PaperTradingValidationError("Stop/Take-Profit dürfen nicht negativ sein.")
        if entry_time is not None and not isinstance(entry_time, datetime):
            raise PaperTradingValidationError("Ungültiger Zeitstempel.")

    def update_market(
        self,
        high: float,
        low: float,
        close: float,
        timestamp: datetime | None,
        trailing_distance: float = 0.0,
    ) -> list[PaperPosition]:
        """Bewertet alle offenen Positionen zu einem neuen Tag (Mark-to-Market).

        Prüft je Position Stop/Take-Profit (Stop hat Vorrang) und schließt sie bei
        Auslösung; sonst wird sie zum Schlusskurs neu bewertet. Der Trailing-Stop
        ist **vorbereitet** (nur aktiv bei ``trailing_distance > 0``).

        Returns:
            Die in diesem Schritt geschlossenen Positionen.
        """
        if not _valid_price(high) or not _valid_price(low) or not _valid_price(close):
            raise PaperTradingValidationError("Ungültige Preise beim Markt-Update.")
        if timestamp is not None and not isinstance(timestamp, datetime):
            raise PaperTradingValidationError("Ungültiger Zeitstempel beim Markt-Update.")

        closed_now: list[PaperPosition] = []
        touched: list[str] = []
        for pid, position in list(self._positions.items()):
            if not position.is_open:
                continue
            touched.append(pid)
            if trailing_distance > 0:
                position = position_mod.apply_trailing_stop(position, close, trailing_distance)
            reason, price = position_mod.detect_exit(position, high, low, close)
            if reason is not None:
                position = position_mod.close_position(position, price, timestamp, reason)
                self._positions[pid] = position
                self._realized_pnl += position.pnl
                self._record_order(position, OrderAction.CLOSE, price, timestamp, reason.value)
                self._journal.record_close(position)
                closed_now.append(position)
            else:
                self._positions[pid] = position_mod.mark_to_market(position, close, timestamp)
        self._recompute(timestamp, touched)
        return closed_now

    def close_position(
        self,
        position_id: str,
        price: float,
        timestamp: datetime | None,
        reason: CloseReason = CloseReason.MANUAL,
    ) -> PaperPosition:
        """Schließt eine bestimmte offene Position manuell/verfallen."""
        position = self._require_position(position_id)
        action = OrderAction.EXPIRE if reason is CloseReason.EXPIRE else OrderAction.CLOSE
        order_mod.ensure_valid_transition(position.status, action)
        if not _valid_price(price):
            raise PaperTradingValidationError("Ungültiger Schließungspreis.")
        closed = position_mod.close_position(position, price, timestamp, reason)
        self._positions[position_id] = closed
        self._realized_pnl += closed.pnl
        self._record_order(closed, action, price, timestamp, reason.value)
        self._journal.record_close(closed)
        self._recompute(timestamp, [position_id])
        return closed

    def cancel_position(self, position_id: str, timestamp: datetime | None) -> PaperPosition:
        """Storniert eine offene Position (kein PnL)."""
        position = self._require_position(position_id)
        order_mod.ensure_valid_transition(position.status, OrderAction.CANCEL)
        cancelled = position_mod.cancel_position(position, timestamp)
        self._positions[position_id] = cancelled
        self._record_order(
            cancelled, OrderAction.CANCEL, position.current_price, timestamp, "cancel"
        )
        self._journal.record_cancel(cancelled, timestamp)
        self._recompute(timestamp, [position_id])
        return cancelled

    # ------------------------------------------------------------------ #
    # Interne Helfer
    # ------------------------------------------------------------------ #

    def _require_position(self, position_id: str) -> PaperPosition:
        """Gibt eine Position zurück oder wirft einen Validierungsfehler."""
        if position_id not in self._positions:
            raise PaperTradingValidationError(f"Unbekannte Position '{position_id}'.")
        return self._positions[position_id]

    def _record_order(
        self,
        position: PaperPosition,
        action: OrderAction,
        price: float,
        timestamp: datetime | None,
        reason: str,
    ) -> None:
        """Legt eine simulierte Order ab (Audit)."""
        self._orders.append(
            order_mod.create_order(position, action, price, timestamp, reason, len(self._orders))
        )

    def _recompute(self, timestamp: datetime | None, touched: list[str]) -> None:
        """Aktualisiert Peak/Drawdown, Kapitalkurve und Positions-Kontext."""
        equity = self.equity()
        self._peak_equity = max(self._peak_equity, equity)
        running_dd = self.running_drawdown_pct()
        self._max_drawdown_pct = max(self._max_drawdown_pct, running_dd)
        self._equity_curve.append(
            PaperEquityPoint(
                timestamp=timestamp,
                equity=equity,
                drawdown_pct=running_dd,
                exposure_pct=self.exposure_pct(),
                open_positions=len(self.open_positions()),
            )
        )
        for pid in touched:
            self._stamp_context(pid)

    def _stamp_context(self, position_id: str) -> None:
        """Friert die aktuellen Portfolio-Kennzahlen für eine Position ein."""
        self._context[position_id] = {
            "current_equity": self.equity(),
            "portfolio_exposure": self.exposure_pct(),
            "running_drawdown": self.running_drawdown_pct(),
            "maximum_drawdown": self._max_drawdown_pct,
        }


def _valid_price(price: float) -> bool:
    """Ob ein Preis gültig ist (endlich und > 0)."""
    return isinstance(price, (int, float)) and price == price and price > 0.0
