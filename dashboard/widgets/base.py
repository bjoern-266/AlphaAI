"""Gemeinsame Schnittstelle und Hilfsmittel für Widgets.

Ein Widget implementiert :class:`BaseWidget` und liefert aus einem
:class:`WidgetContext` eine :class:`~models.dashboard.WidgetSpec`. Widgets
**berechnen nichts**; sie lesen das View Model und formatieren es. Sie sind
unabhängig voneinander (kein Widget importiert ein anderes) – gemeinsame
Formatier-Bausteine liegen in :mod:`dashboard.widgets.common`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from dashboard.settings import DashboardSettings
from dashboard.state import DashboardState
from dashboard.theme import Theme
from dashboard.viewmodels import DashboardViewModel
from models.dashboard import WidgetSpec


@dataclass(frozen=True, slots=True)
class WidgetContext:
    """Eingabe eines Widgets (unveränderlich).

    Attributes:
        view_model: Die abgelesenen Report-Werte (keine Berechnung).
        theme: Das aktive Theme (alle Gestaltungswerte).
        settings: Die Anzeigeeinstellungen.
        state: Der aktuelle Dashboard-Zustand (Filter/Sortierung/…).
    """

    view_model: DashboardViewModel
    theme: Theme
    settings: DashboardSettings
    state: DashboardState


class BaseWidget(ABC):
    """Basisklasse für alle Widgets.

    Attributes:
        name: Eindeutiger Widget-Name (= Schlüssel in der Registry/im Router).
        title: Standard-Anzeigetitel.
        icon: Semantischer Icon-Name (aus dem Theme).
    """

    name: str = "base"
    title: str = ""
    icon: str = ""

    @abstractmethod
    def build(self, context: WidgetContext) -> WidgetSpec:
        """Baut die Anzeige-Beschreibung dieses Widgets (ohne Berechnung)."""
        raise NotImplementedError
