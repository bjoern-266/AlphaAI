"""Dashboard Engine – setzt aus Reports und Zustand eine Ansicht zusammen.

Die :class:`DashboardEngine` verbindet View Model, Router und Widget-Registry zu
einer :class:`~models.dashboard.DashboardView`. Sie **berechnet nichts**,
**verändert nichts** und enthält **keine** Fachlogik – sie liest das View Model
und ruft die (unabhängigen) Widgets auf. Sie muss für **neue** Widgets oder
Seiten **nie** geändert werden: Widgets kommen über die Registry, Seiten über den
Router hinzu (Open/Closed).

Fehler eines einzelnen Widgets werden isoliert als Anzeige-Zustand behandelt
(keine Exceptions im Frontend). Lade-/Fehlerzustände des ``DashboardState``
führen zu einer entsprechenden Anzeige.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from core.logging_config import get_logger
from dashboard.feedback import error_spec, loading_spec
from dashboard.responsive import adapt_regions
from dashboard.router import Router, build_default_router
from dashboard.settings import DashboardSettings, load_dashboard_settings
from dashboard.state import DashboardState, ErrorState, LoadingState
from dashboard.theme import Theme, load_theme
from dashboard.viewmodels import ReportBundle, build_view_model
from dashboard.widget_registry import WidgetRegistry, build_default_registry
from dashboard.widgets.base import WidgetContext
from models.dashboard import KIND_TEXT, DashboardView, WidgetSpec

_logger = get_logger(__name__)


class DashboardEngine:
    """Setzt die aktuelle Dashboard-Ansicht zusammen (reine Präsentation).

    Args:
        theme: Das aktive Theme (alle Gestaltungswerte).
        settings: Die Anzeigeeinstellungen.
        registry: Widget-Registry (Standard: alle Standard-Widgets).
        router: Router mit den Seiten-Layouts (Standard: alle Seiten).
    """

    def __init__(
        self,
        theme: Theme,
        settings: DashboardSettings,
        registry: WidgetRegistry | None = None,
        router: Router | None = None,
    ) -> None:
        self._theme = theme
        self._settings = settings
        self._registry = registry or build_default_registry()
        self._router = router or build_default_router()

    @classmethod
    def from_config(cls, settings_path: Path | None = None) -> DashboardEngine:
        """Erzeugt eine Engine mit Standard-Theme und -Einstellungen."""
        return cls(theme=load_theme(), settings=load_dashboard_settings(settings_path))

    @property
    def router(self) -> Router:
        """Der Router (für Navigation/Seiten)."""
        return self._router

    @property
    def theme(self) -> Theme:
        """Das aktive Theme."""
        return self._theme

    def build_view(self, state: DashboardState, bundle: ReportBundle) -> DashboardView:
        """Baut die :class:`DashboardView` für den aktuellen Zustand.

        Reihenfolge:
        1. Lade-/Fehlerzustand → Feedback-Ansicht (keine Berechnung),
        2. sonst: View Model ablesen, Layout auflösen, Widgets aufrufen.
        """
        layout = self._router.resolve(state.active_page)
        if state.loading_state is not LoadingState.IDLE:
            return self._feedback_view(state, layout.title, loading_spec(state.loading_state))
        if state.error_state is not ErrorState.NONE:
            return self._feedback_view(state, layout.title, error_spec(state.error_state))

        view_model = build_view_model(bundle)
        context = WidgetContext(
            view_model=view_model, theme=self._theme, settings=self._settings, state=state
        )
        regions = adapt_regions(dict(layout.regions), state.device_class)

        widgets: dict[str, WidgetSpec] = {}
        warnings: list[str] = []
        for widget_id in _ids(regions):
            if widget_id not in self._registry:
                warnings.append(f"Widget '{widget_id}' ist nicht registriert.")
                continue
            widgets[widget_id] = self._safe_build(widget_id, context, warnings)

        return DashboardView(
            page=state.active_page.value,
            title=layout.title,
            regions={region: ids for region, ids in regions.items()},
            widgets=widgets,
            device_class=state.device_class.value,
            valid=not warnings,
            warnings=tuple(warnings),
            generated_at=datetime.now(UTC),
        )

    def _safe_build(
        self, widget_id: str, context: WidgetContext, warnings: list[str]
    ) -> WidgetSpec:
        """Baut ein Widget und fängt Fehler als Anzeige-Zustand ab."""
        try:
            return self._registry.get(widget_id).build(context)
        except Exception as error:  # Keine Exceptions im Frontend.
            _logger.warning("Widget '%s' fehlgeschlagen: %s", widget_id, error)
            warnings.append(f"Widget '{widget_id}' fehlgeschlagen: {error}")
            return WidgetSpec(
                widget_id=widget_id,
                title=widget_id,
                kind=KIND_TEXT,
                text="Fehler bei der Anzeige.",
                placeholder=True,
            )

    def _feedback_view(self, state: DashboardState, title: str, spec: WidgetSpec) -> DashboardView:
        """Baut eine reine Feedback-Ansicht (Laden/Fehler)."""
        return DashboardView(
            page=state.active_page.value,
            title=title,
            regions={"center": (spec.widget_id,)},
            widgets={spec.widget_id: spec},
            device_class=state.device_class.value,
            valid=False,
            warnings=(spec.text,) if spec.text else (),
            generated_at=datetime.now(UTC),
        )


def _ids(regions: dict[str, tuple[str, ...]]) -> tuple[str, ...]:
    """Alle Widget-IDs einer Regionen-Zuordnung in Reihenfolge left/center/right."""
    ordered: list[str] = []
    for region in ("left", "center", "right"):
        ordered.extend(regions.get(region, ()))
    return tuple(ordered)
