"""Widgets des AlphaAI Command Center.

Jedes Widget ist **vollständig unabhängig** und liefert ausschließlich eine
:class:`~models.dashboard.WidgetSpec` (eine Beschreibung, *was* angezeigt werden
soll). Ein Widget **berechnet nichts** und **verändert nichts** – es liest nur
das :class:`~dashboard.viewmodels.DashboardViewModel` ab und formatiert es für die
Anzeige. Neue Widgets werden ausschließlich über ``widget_registry.py``
registriert; die :class:`~dashboard.engine.DashboardEngine` bleibt unverändert.
"""
