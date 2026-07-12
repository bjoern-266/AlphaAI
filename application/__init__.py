"""Application Service Layer – der produktive Backend-Kern von AlphaAI.

Diese Schicht macht das gesamte, unveränderte Analyse-System als produktiven
Backend-Dienst verfügbar. Sie besteht aus klar getrennten Bausteinen:

* ``exceptions`` – die Fehlerhierarchie der Application-Schicht,
* ``serialization`` – wandelt bestehende (frozen) Reports in JSON-fähige Daten,
* ``repositories`` – dauerhafte Persistenz der Reports (SQLite),
* ``responses`` – einheitliche API-Antwort-Hüllen (Envelope),
* ``services`` – lesen gespeicherte Reports und betreiben den Hintergrunddienst,
* ``health`` – aggregiertes Health-Monitoring,
* ``authentication`` – vorbereitete Zugriffskontrolle (vorerst nur lokal),
* ``api`` – die produktionsreife, framework-unabhängige REST-API.

Grundsatz: Die Application-Schicht **liest** ausschließlich vorhandene Reports.
Sie berechnet nichts, trifft keine Handelsentscheidung und ändert keine Engine.
Sie importiert nur ``models`` und ``core`` – die eigentliche Pipeline wird
injiziert (Dependency Injection), damit keine Import-Zyklen entstehen.
"""

from __future__ import annotations

__all__: list[str] = []
