"""Domänenmodell: Marktdaten.

Enthält das kanonische Spaltenschema und das unveränderliche Ergebnisobjekt
:class:`MarketResult` der Data Layer. Dieses Modul ist Teil der Entities-Schicht
(``models/``) und importiert **nichts** aus höheren Schichten (Engines, Data,
Provider) – dadurch bleibt die Abhängigkeitsrichtung strikt abwärts.

Aus Gründen der Rückwärtskompatibilität wird der Inhalt zusätzlich unter
``data.market_result`` re-exportiert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd

# Kanonische Spaltennamen. Jeder Provider normalisiert seine Rohdaten auf
# genau dieses Schema, sodass nachgelagerte Module keine Provider-Details
# kennen müssen.
COL_OPEN = "open"
COL_HIGH = "high"
COL_LOW = "low"
COL_CLOSE = "close"
COL_ADJ_CLOSE = "adj_close"
COL_VOLUME = "volume"

OHLCV_COLUMNS: tuple[str, ...] = (
    COL_OPEN,
    COL_HIGH,
    COL_LOW,
    COL_CLOSE,
    COL_ADJ_CLOSE,
    COL_VOLUME,
)


class MarketStatus(Enum):
    """Statuscode eines Marktdatenergebnisses.

    Attributes:
        OK: Alle angeforderten Symbole wurden erfolgreich geladen.
        PARTIAL: Ein Teil der Symbole fehlt oder ist ungültig.
        EMPTY: Es wurden keine Daten geliefert.
        ERROR: Die Abfrage ist vollständig fehlgeschlagen.
    """

    OK = "ok"
    PARTIAL = "partial"
    EMPTY = "empty"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class MarketResult:
    """Ergebnis einer Marktdatenanfrage (unveränderlich).

    Die Identität des Objekts (Provider, Status) ist nach der Erstellung fest.
    Die enthaltenen Sammlungen (``data``, ``metadata``, ``errors``) werden
    während der Zusammenstellung durch die Data Layer befüllt.

    Attributes:
        provider: Name des Providers, der die Daten geliefert hat.
        status: Statuscode des Ergebnisses.
        data: Zuordnung Symbol -> DataFrame mit dem kanonischen OHLCV-Schema
            (Spalten in :data:`OHLCV_COLUMNS`, Index = Zeitstempel).
        metadata: Zusätzliche Informationen (z. B. Zeitraum, Intervall).
        errors: Liste menschenlesbarer Fehlermeldungen.
    """

    provider: str
    status: MarketStatus
    data: dict[str, pd.DataFrame] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def symbols(self) -> list[str]:
        """Gibt die enthaltenen Symbole zurück."""
        return list(self.data.keys())

    @property
    def is_ok(self) -> bool:
        """Gibt zurück, ob alle Symbole erfolgreich geladen wurden."""
        return self.status is MarketStatus.OK

    def frame(self, symbol: str) -> pd.DataFrame | None:
        """Gibt den DataFrame eines Symbols zurück oder ``None``.

        Args:
            symbol: Symbol (Groß-/Kleinschreibung wird angeglichen).
        """
        return self.data.get(symbol.strip().upper())

    def add_error(self, message: str) -> None:
        """Fügt eine Fehlermeldung hinzu (Inhalt der ``errors``-Liste)."""
        self.errors.append(message)

    @classmethod
    def empty(cls, provider: str, metadata: dict[str, Any] | None = None) -> MarketResult:
        """Erzeugt ein leeres Ergebnis (keine Daten, Status EMPTY)."""
        return cls(provider=provider, status=MarketStatus.EMPTY, metadata=metadata or {})

    @classmethod
    def error(
        cls, provider: str, message: str, metadata: dict[str, Any] | None = None
    ) -> MarketResult:
        """Erzeugt ein Fehlerergebnis (Status ERROR) mit einer Meldung."""
        return cls(
            provider=provider,
            status=MarketStatus.ERROR,
            metadata=metadata or {},
            errors=[message],
        )
