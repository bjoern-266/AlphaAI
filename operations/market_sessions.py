"""Definition der Marktsitzungen (Phasen je Markt, aus der Konfiguration).

Ein Markt (z. B. Europa/USA) hat eine Zeitzone und geordnete Phasen (Vorbörse,
Öffnung, Nachmittag, Schluss, …). Alle Zeiten sind **ausschließlich
konfigurierbar**; Sommer-/Winterzeit wird über die IANA-Zeitzone automatisch
berücksichtigt. Es findet **keine** Fachlogik statt – nur die Struktur der
Sitzungen.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from core.exceptions import AlphaAIError


class MarketSessionError(AlphaAIError):
    """Wird ausgelöst, wenn eine Marktsitzung ungültig konfiguriert ist."""


@dataclass(frozen=True, slots=True)
class Phase:
    """Eine Marktphase (unveränderlich).

    Attributes:
        name: Name der Phase (z. B. ``"open"``).
        start_minute: Startzeit als Minuten seit Mitternacht (lokale Marktzeit).
        is_open: Ob der Markt in dieser Phase als geöffnet gilt.
    """

    name: str
    start_minute: int
    is_open: bool


@dataclass(frozen=True, slots=True)
class MarketSession:
    """Die Sitzung eines Marktes (unveränderlich).

    Attributes:
        key: Markt-Schlüssel (z. B. ``"europe"``).
        title: Anzeigename.
        timezone: IANA-Zeitzone (z. B. ``"Europe/Berlin"``).
        phases: Nach Startzeit geordnete Phasen.
    """

    key: str
    title: str
    timezone: str
    phases: tuple[Phase, ...]


def parse_time(value: str) -> int:
    """Wandelt ``"HH:MM"`` in Minuten seit Mitternacht um.

    Raises:
        MarketSessionError: Wenn das Format oder der Wertebereich ungültig ist.
    """
    parts = str(value).split(":")
    if len(parts) != 2:
        raise MarketSessionError(f"Ungültige Uhrzeit '{value}' (erwartet HH:MM).")
    try:
        hour, minute = int(parts[0]), int(parts[1])
    except ValueError as error:
        raise MarketSessionError(f"Ungültige Uhrzeit '{value}'.") from error
    if not (0 <= hour < 24 and 0 <= minute < 60):
        raise MarketSessionError(f"Uhrzeit '{value}' außerhalb des gültigen Bereichs.")
    return hour * 60 + minute


def _validate_timezone(timezone: str) -> str:
    """Prüft, dass eine Zeitzone existiert (Sommer-/Winterzeit inklusive)."""
    try:
        ZoneInfo(timezone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise MarketSessionError(f"Ungültige Zeitzone '{timezone}'.") from error
    return timezone


def build_session(key: str, config: Mapping[str, Any]) -> MarketSession:
    """Baut eine :class:`MarketSession` aus der Konfiguration eines Marktes.

    Raises:
        MarketSessionError: Wenn Phasen/Zeiten/Zeitzone ungültig sind.
    """
    timezone = _validate_timezone(str(config.get("timezone", "UTC")))
    raw_phases = config.get("phases", [])
    if not isinstance(raw_phases, Sequence) or not raw_phases:
        raise MarketSessionError(f"Markt '{key}' hat keine Phasen.")
    phases: list[Phase] = []
    for entry in raw_phases:
        if not isinstance(entry, Sequence) or len(entry) != 3:
            raise MarketSessionError(f"Markt '{key}': Phase muss [name, HH:MM, is_open] sein.")
        name, start, is_open = entry
        phases.append(Phase(name=str(name), start_minute=parse_time(start), is_open=bool(is_open)))
    phases.sort(key=lambda phase: phase.start_minute)
    return MarketSession(
        key=key, title=str(config.get("title", key)), timezone=timezone, phases=tuple(phases)
    )


def load_sessions(markets: Mapping[str, Any]) -> tuple[MarketSession, ...]:
    """Baut alle Marktsitzungen aus der ``[markets]``-Konfiguration."""
    if not markets:
        raise MarketSessionError("Keine Märkte konfiguriert.")
    return tuple(build_session(key, config) for key, config in markets.items())
