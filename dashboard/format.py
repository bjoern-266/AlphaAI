"""Reine Anzeige-Formatierung für das Dashboard.

Diese Funktionen wandeln **bereits vorhandene** Werte in Text um (Währung,
Prozent, Zahlen, Vorzeichen, Platzhalter). Sie **berechnen nichts** und leiten
keine neuen Kennzahlen ab – sie formatieren ausschließlich für die Anzeige.
Fehlt ein Wert (``None``), wird der Platzhalter angezeigt (keine
Ersatzberechnung).
"""

from __future__ import annotations

import math

PLACEHOLDER = "—"


def na(value: object) -> bool:
    """Ob ein Wert als „nicht verfügbar" gilt (``None`` oder ``NaN``)."""
    if value is None:
        return True
    return isinstance(value, float) and math.isnan(value)


def text(value: object) -> str:
    """Gibt einen Wert als Text zurück (Platzhalter bei fehlendem Wert)."""
    return PLACEHOLDER if na(value) else str(value)


def number(value: float | int | None, decimals: int = 2) -> str:
    """Formatiert eine Zahl mit fester Nachkommastelle (Platzhalter bei ``None``)."""
    if na(value):
        return PLACEHOLDER
    if isinstance(value, float) and math.isinf(value):
        return "∞"
    return f"{value:,.{decimals}f}"


def integer(value: float | int | None) -> str:
    """Formatiert eine Ganzzahl (Platzhalter bei fehlendem Wert)."""
    if na(value):
        return PLACEHOLDER
    return f"{int(value):,d}"


def currency(value: float | int | None, symbol: str = "€", decimals: int = 2) -> str:
    """Formatiert einen Geldbetrag als Text (Platzhalter bei fehlendem Wert)."""
    if na(value):
        return PLACEHOLDER
    return f"{value:,.{decimals}f} {symbol}"


def signed_currency(value: float | int | None, symbol: str = "€", decimals: int = 2) -> str:
    """Formatiert einen Geldbetrag mit explizitem Vorzeichen."""
    if na(value):
        return PLACEHOLDER
    return f"{value:+,.{decimals}f} {symbol}"


def percent(value: float | int | None, decimals: int = 1) -> str:
    """Formatiert einen **bereits** in Prozent vorliegenden Wert (0..100)."""
    if na(value):
        return PLACEHOLDER
    if isinstance(value, float) and math.isinf(value):
        return "∞"
    return f"{value:,.{decimals}f} %"


def ratio_as_percent(value: float | int | None, decimals: int = 1) -> str:
    """Formatiert einen Anteil (0..1) als Prozenttext.

    Die Multiplikation mit 100 ist eine reine **Darstellungs**-Umrechnung des
    bereits vorhandenen Werts – keine Kennzahlenberechnung.
    """
    if na(value):
        return PLACEHOLDER
    return f"{value * 100:,.{decimals}f} %"


def signed_percent(value: float | int | None, decimals: int = 2) -> str:
    """Formatiert einen Prozentwert (0..100) mit explizitem Vorzeichen."""
    if na(value):
        return PLACEHOLDER
    return f"{value:+,.{decimals}f} %"


def profit_factor(value: float | int | None, decimals: int = 2) -> str:
    """Formatiert den Profit Factor (``∞`` ohne Verluste)."""
    return number(value, decimals)


def duration(seconds: float | int | None) -> str:
    """Formatiert eine Dauer/Countdown in Sekunden als ``H:MM:SS`` (Anzeige)."""
    if na(seconds):
        return PLACEHOLDER
    total = int(seconds)
    sign = "-" if total < 0 else ""
    total = abs(total)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{sign}{hours}:{minutes:02d}:{secs:02d}"


def clock_time(value: object) -> str:
    """Formatiert einen Zeitstempel als ``HH:MM`` (Platzhalter bei ``None``)."""
    if na(value):
        return PLACEHOLDER
    try:
        return value.strftime("%H:%M")  # type: ignore[attr-defined]
    except AttributeError:
        return str(value)
