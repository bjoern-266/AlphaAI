"""Lade- und Fehlerzustände (nur Anzeige, keine Exceptions im Frontend).

Baut aus den Zuständen :class:`~dashboard.state.LoadingState` und
:class:`~dashboard.state.ErrorState` reine Anzeige-Widgets (Skeleton/Progress
bzw. Fehlermeldung). Es findet **keine** Berechnung statt; Fehler werden als
Zustand **angezeigt**, niemals als Exception geworfen.
"""

from __future__ import annotations

from dashboard.state import ErrorState, LoadingState
from models.dashboard import KIND_TEXT, TONE_DANGER, TONE_INFO, TONE_WARNING, WidgetSpec

ERROR_MESSAGES: dict[ErrorState, str] = {
    ErrorState.NONE: "",
    ErrorState.LOADING: "Lädt Reports …",
    ErrorState.OFFLINE: "Offline – keine Verbindung zu den Daten.",
    ErrorState.NO_DATA: "Keine Daten vorhanden.",
    ErrorState.DISCONNECTED: "Verbindung getrennt.",
    ErrorState.TIMEOUT: "Zeitüberschreitung beim Laden.",
    ErrorState.ERROR: "Ein Fehler ist aufgetreten.",
}

_ERROR_TONE: dict[ErrorState, str] = {
    ErrorState.LOADING: TONE_INFO,
    ErrorState.OFFLINE: TONE_DANGER,
    ErrorState.NO_DATA: TONE_WARNING,
    ErrorState.DISCONNECTED: TONE_DANGER,
    ErrorState.TIMEOUT: TONE_WARNING,
    ErrorState.ERROR: TONE_DANGER,
}

_LOADING_TEXT: dict[LoadingState, str] = {
    LoadingState.SKELETON: "Skeleton",
    LoadingState.PROGRESS: "Progress",
    LoadingState.FADE: "Fade",
}


def error_spec(error_state: ErrorState) -> WidgetSpec:
    """Baut ein Fehler-Widget (Platzhalter mit Meldung)."""
    message = ERROR_MESSAGES.get(error_state, ERROR_MESSAGES[ErrorState.ERROR])
    return WidgetSpec(
        widget_id="error_state",
        title="Status",
        kind=KIND_TEXT,
        text=message,
        placeholder=True,
        metadata={
            "error_state": error_state.value,
            "tone": _ERROR_TONE.get(error_state, TONE_DANGER),
        },
    )


def loading_spec(loading_state: LoadingState) -> WidgetSpec:
    """Baut ein Lade-Widget (Skeleton/Progress/Fade – nie eine leere Seite)."""
    return WidgetSpec(
        widget_id="loading_state",
        title="Loading",
        kind=KIND_TEXT,
        text=_LOADING_TEXT.get(loading_state, "Skeleton"),
        placeholder=True,
        metadata={"loading_state": loading_state.value},
    )
