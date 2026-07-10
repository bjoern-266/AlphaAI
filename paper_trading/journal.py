"""Automatisches Journal für das simulierte Portfolio.

Der :class:`PaperJournal` dokumentiert **jeden** simulierten Trade automatisch
beim Eröffnen und Schließen (sowie beim Stornieren/Verfallen). Jeder
:class:`~models.paper_trading.JournalEntry` enthält mindestens Ein-/Ausstieg,
Grund, PnL, Recommendation-ID, Richtung, Stärke sowie Reasons und Warnings – die
Entscheidungen bleiben damit vollständig nachvollziehbar.

Der Journal-Manager ist ein einfacher, zustandsbehafteter Sammler; die einzelnen
Einträge sind unveränderlich.
"""

from __future__ import annotations

from datetime import datetime

from models.paper_trading import (
    JournalEntry,
    OrderAction,
    PaperPosition,
)


class PaperJournal:
    """Sammelt unveränderliche Journal-Einträge in Reihenfolge ihres Auftretens."""

    def __init__(self) -> None:
        self._entries: list[JournalEntry] = []

    def record_open(self, position: PaperPosition, timestamp: datetime | None) -> JournalEntry:
        """Dokumentiert die Eröffnung einer Position."""
        return self._append(
            position,
            OrderAction.OPEN,
            reason=f"Eröffnet zu {position.entry_price:.2f} ({position.direction.value}).",
            exit_price=0.0,
            pnl=0.0,
            timestamp=timestamp,
        )

    def record_close(self, position: PaperPosition) -> JournalEntry:
        """Dokumentiert das Schließen einer Position (Stop/Take-Profit/Expire)."""
        reason_label = position.close_reason.value if position.close_reason else "close"
        action = OrderAction.EXPIRE if reason_label == "expire" else OrderAction.CLOSE
        return self._append(
            position,
            action,
            reason=f"Geschlossen zu {position.exit_price:.2f} (Grund: {reason_label}).",
            exit_price=position.exit_price,
            pnl=position.pnl,
            timestamp=position.exit_time,
        )

    def record_cancel(self, position: PaperPosition, timestamp: datetime | None) -> JournalEntry:
        """Dokumentiert das Stornieren einer Position."""
        return self._append(
            position,
            OrderAction.CANCEL,
            reason="Storniert (kein Einstieg).",
            exit_price=0.0,
            pnl=0.0,
            timestamp=timestamp,
        )

    def _append(
        self,
        position: PaperPosition,
        action: OrderAction,
        reason: str,
        exit_price: float,
        pnl: float,
        timestamp: datetime | None,
    ) -> JournalEntry:
        """Erzeugt und speichert einen Journal-Eintrag."""
        entry = JournalEntry(
            entry_id=f"journal:{len(self._entries)}",
            position_id=position.position_id,
            recommendation_id=position.recommendation_id,
            action=action,
            direction=position.direction,
            recommendation_strength=position.recommendation_strength,
            entry_price=position.entry_price,
            exit_price=exit_price,
            reason=reason,
            pnl=pnl,
            reasons=list(position.reasons),
            warnings=list(position.warnings),
            timestamp=timestamp,
        )
        self._entries.append(entry)
        return entry

    def entries(self) -> list[JournalEntry]:
        """Gibt eine Kopie aller Journal-Einträge zurück."""
        return list(self._entries)

    def __len__(self) -> int:
        """Anzahl der Journal-Einträge."""
        return len(self._entries)
