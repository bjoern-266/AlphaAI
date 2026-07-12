"""Branchen-Ausgleich der Ergebnisliste (konfigurierbar, keine festen Limits).

Verhindert eine einseitige Ergebnisliste: sind viele Werte derselben Branche
gleichzeitig stark bewertet, verteilt der Balancer die Liste nach Möglichkeit auf
verschiedene Branchen. Er **berechnet nichts** – er ordnet bereits bewertete
Chancen um. Das Verhalten ist vollständig konfigurierbar; ohne Aktivierung bleibt
die Score-Reihenfolge unverändert.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from models.opportunity import Opportunity


@dataclass(frozen=True, slots=True)
class BalanceConfig:
    """Konfiguration des Branchen-Ausgleichs (unveränderlich).

    Attributes:
        enabled: Ob der Ausgleich aktiv ist.
        max_streak: Höchstzahl direkt aufeinanderfolgender Werte derselben Branche,
            bevor – falls vorhanden – ein Wert einer anderen Branche vorgezogen wird.
    """

    enabled: bool = True
    max_streak: int = 2


def load_balance_config(config: Mapping[str, Any]) -> BalanceConfig:
    """Baut die Ausgleichs-Konfiguration aus der Regel-Konfiguration."""
    return BalanceConfig(
        enabled=bool(config.get("enabled", True)),
        max_streak=int(config.get("max_streak", 2)),
    )


def balance(opportunities: Sequence[Opportunity], config: BalanceConfig) -> tuple[Opportunity, ...]:
    """Ordnet die (score-sortierten) Chancen nach Branchen aus.

    Solange eine Branche nicht öfter als ``max_streak`` direkt hintereinander
    erscheint, bleibt die Score-Reihenfolge erhalten. Andernfalls wird die
    höchstbewertete Chance einer **anderen** Branche vorgezogen (fällt keine an,
    bleibt die Score-Reihenfolge bestehen).
    """
    if not config.enabled or config.max_streak <= 0:
        return tuple(opportunities)

    remaining = list(opportunities)
    result: list[Opportunity] = []
    streak_sector: str | None = None
    streak = 0
    while remaining:
        index = 0
        if streak_sector is not None and streak >= config.max_streak:
            other = next((i for i, o in enumerate(remaining) if o.sector != streak_sector), None)
            if other is not None:
                index = other
        chosen = remaining.pop(index)
        if chosen.sector == streak_sector:
            streak += 1
        else:
            streak_sector = chosen.sector
            streak = 1
        result.append(chosen)
    return tuple(result)
