"""Kernschicht von Alpha AI.

Dieses Paket enthält technische Grundbausteine, die von allen anderen
Modulen benötigt werden und selbst keine fachliche (Trading-)Logik tragen:

- ``paths``          – zentrale Verzeichnis- und Dateipfade des Projekts.
- ``exceptions``     – projektweite Fehlerklassen.
- ``config``         – Laden und Validieren der ``settings.toml``.
- ``logging_config`` – einheitliche Logging-Konfiguration.

Die Kernschicht kennt keine höheren Schichten (Scanner, Strategien,
Dashboard) und bleibt dadurch frei von Abhängigkeiten in Richtung Fachlogik.
"""
