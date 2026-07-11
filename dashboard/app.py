"""Streamlit-Einstiegspunkt des AlphaAI Command Center (dünne UI-Glue-Schicht).

Diese Datei ist der **einzige** ausführbare Streamlit-Einstieg. Sie enthält
**keine** Fachlogik und **keine** Berechnung: sie baut die
:class:`~dashboard.engine.DashboardEngine`, hält den :class:`DashboardState` in
der Streamlit-Session (damit er **nie verloren geht**), lädt bei Bedarf neue
Reports (Auto-Refresh lädt **nur** Reports, startet **keine** Berechnung) und
übergibt die fertige Ansicht an die Renderschicht.

Fehlt Streamlit in der Umgebung, wird diese Datei schlicht nicht importiert –
die gesamte Dashboard-Logik ist Streamlit-frei und vollständig testbar. Deshalb
ist der Streamlit-Import bewusst **lazy** (innerhalb der Funktionen) und der
Modulinhalt von der Testabdeckung ausgenommen (``pragma: no cover``).
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from dashboard.engine import DashboardEngine
from dashboard.render import render_view
from dashboard.state import DashboardState, DeviceClass, Page, RefreshRate
from dashboard.viewmodels import ReportBundle

# Schlüssel des Zustands-Snapshots in der Streamlit-Session.
_STATE_KEY = "alphaai_dashboard_state"


def _load_reports() -> ReportBundle:  # pragma: no cover - IO-Glue
    """Lädt die aktuellen Reports (Auto-Refresh lädt **nur** Reports).

    In dieser Ausbaustufe liegen keine persistierten Reports vor; das Dashboard
    zeigt dann Platzhalter/„offline" an (es wird **nichts** ersatzweise
    berechnet). Sobald Reports gespeichert werden, wird hier ausschließlich
    **geladen** – niemals eine Berechnung gestartet.
    """
    return ReportBundle()


def _restore_state(
    session: MutableMapping[str, Any],
) -> DashboardState:  # pragma: no cover - UI-Glue
    """Stellt den Zustand aus der Session wieder her (State geht nie verloren)."""
    state = DashboardState()
    snapshot = session.get(_STATE_KEY)
    if isinstance(snapshot, dict):
        state.restore(snapshot)
    return state


def _persist_state(
    session: MutableMapping[str, Any], state: DashboardState
) -> None:  # pragma: no cover - UI-Glue
    """Sichert den Zustand als Snapshot in der Session."""
    session[_STATE_KEY] = state.snapshot()


def main() -> None:  # pragma: no cover - UI-Glue
    """Rendert das Command Center (dünner Streamlit-Einstieg)."""
    import streamlit as st

    engine = DashboardEngine.from_config()
    theme = engine.theme

    st.set_page_config(page_title="Command Center", layout="wide")

    state = _restore_state(st.session_state)

    # Sidebar-Navigation (nur Navigation – keine Fachlogik).
    with st.sidebar:
        st.caption("Command Center")
        for nav in engine.router.nav_items(theme.icons):
            if st.button(nav.title, key=f"nav_{nav.page.value}", use_container_width=True):
                state.set_page(nav.page)
        options = {f"{r.value} s" if r.value else "Manuell": r for r in RefreshRate}
        choice = st.selectbox("Auto-Refresh", tuple(options), index=0)
        state.set_refresh_rate(options[choice])
        devices = {d.value: d for d in DeviceClass}
        device_choice = st.selectbox("Ansicht", tuple(devices), index=0)
        state.set_device(devices[device_choice])
        state.set_search(st.text_input("Suche", value=state.search_query))
        if st.button("Refresh", key="refresh"):
            st.rerun()

    bundle = _load_reports()
    view = engine.build_view(state, bundle)
    render_view(view, theme)

    _persist_state(st.session_state, state)

    # Auto-Refresh: lädt beim nächsten Lauf nur neue Reports (keine Berechnung).
    if state.refresh_rate is not RefreshRate.MANUAL:
        st.caption(f"Auto-Refresh: alle {state.refresh_rate.value} s")


def _default_page() -> Page:  # pragma: no cover - UI-Glue
    """Die Standard-Startseite (aus dem Zustand abgeleitet)."""
    return Page.OVERVIEW


if __name__ == "__main__":  # pragma: no cover - Skript-Einstieg
    main()
