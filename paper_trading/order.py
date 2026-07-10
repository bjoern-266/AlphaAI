"""Order-Management für das simulierte Portfolio.

Erzeugt :class:`~models.paper_trading.PaperOrder`-Einträge (reine Dokumentation –
**keine** echte Order) und prüft die zulässigen **Statuswechsel** einer Position.
Zulässig sind ausschließlich Übergänge einer **offenen** Position:

* ``OPEN``   – eine neue Position eröffnen (nur wenn noch keine existiert),
* ``CLOSE``  – eine offene Position schließen,
* ``CANCEL`` – eine offene Position stornieren (→ CANCELLED),
* ``EXPIRE`` – eine offene Position verfallen lassen (→ CLOSED, Grund Expire).

Eine bereits geschlossene oder stornierte Position kann **nicht** erneut
verändert werden.
"""

from __future__ import annotations

from datetime import datetime

from core.exceptions import PaperTradingValidationError
from models.paper_trading import (
    OrderAction,
    PaperOrder,
    PaperPosition,
    PositionStatus,
)

# Zielstatus je Aktion (für die Übergangsprüfung offener Positionen).
_ACTION_TARGET: dict[OrderAction, PositionStatus] = {
    OrderAction.CLOSE: PositionStatus.CLOSED,
    OrderAction.EXPIRE: PositionStatus.CLOSED,
    OrderAction.CANCEL: PositionStatus.CANCELLED,
}


def is_valid_transition(status: PositionStatus, action: OrderAction) -> bool:
    """Prüft, ob eine Aktion auf eine Position mit ``status`` zulässig ist.

    * ``OPEN`` ist nur für eine noch **nicht** existierende Position gedacht und
      daher auf eine bestehende Position nie gültig.
    * ``CLOSE``/``CANCEL``/``EXPIRE`` sind nur auf einer **offenen** Position
      gültig.
    """
    if action is OrderAction.OPEN:
        return False
    return status is PositionStatus.OPEN


def ensure_valid_transition(status: PositionStatus, action: OrderAction) -> None:
    """Wirft :class:`PaperTradingValidationError`, wenn der Wechsel ungültig ist."""
    if not is_valid_transition(status, action):
        raise PaperTradingValidationError(
            f"Ungültiger Statuswechsel: {action.value} auf Position im Status " f"'{status.value}'."
        )


def target_status(action: OrderAction) -> PositionStatus:
    """Gibt den Zielstatus einer schließenden/stornierenden Aktion zurück."""
    if action not in _ACTION_TARGET:
        raise PaperTradingValidationError(f"Aktion '{action.value}' hat keinen Zielstatus.")
    return _ACTION_TARGET[action]


def create_order(
    position: PaperPosition,
    action: OrderAction,
    price: float,
    timestamp: datetime | None,
    reason: str,
    sequence: int = 0,
) -> PaperOrder:
    """Erzeugt eine simulierte Order zu einer Position (Audit/Journal).

    Args:
        position: Die betroffene Position.
        action: Aktion (OPEN/CLOSE/CANCEL/EXPIRE).
        price: Simulierter Preis der Order.
        timestamp: Zeitpunkt der Order.
        reason: Menschenlesbarer Grund.
        sequence: Laufende Nummer für einen eindeutigen Order-Bezeichner.
    """
    return PaperOrder(
        order_id=f"ord:{position.position_id}:{action.value}:{sequence}",
        recommendation_id=position.recommendation_id,
        position_id=position.position_id,
        action=action,
        direction=position.direction,
        recommendation_strength=position.recommendation_strength,
        price=price,
        shares=position.shares,
        timestamp=timestamp,
        reason=reason,
    )
