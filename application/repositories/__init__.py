"""Dauerhafte Persistenz der Reports (Produktionsspeicher).

Die Reports werden in einer eingebetteten, produktionsgeeigneten SQLite-Datenbank
gespeichert. Dadurch überleben sie einen Neustart des Dienstes, es entstehen
**keine** temporären Dateien und die Lösung ist **nicht** rein im Arbeitsspeicher.
Dashboard und API liefern jederzeit den zuletzt erfolgreich gespeicherten Stand.
"""

from __future__ import annotations

from application.repositories.report_store import ReportStore

__all__ = ["ReportStore"]
