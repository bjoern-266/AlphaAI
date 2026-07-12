"""Produktionsreife, framework-unabhängige REST-API.

Der Kern der API (Routing, Request/Response, Fehlerbehandlung, Cache) ist
bewusst **ohne** Web-Framework umgesetzt und daher vollständig testbar. Ein
dünner Adapter bindet die API bei Bedarf an FastAPI/uvicorn an, ohne dass der
Kern davon abhängt (dieselbe Trennung wie beim streamlit-freien Dashboard).

Die API **stellt ausschließlich vorhandene Reports bereit**. Sie führt keine
Analyse aus, berechnet nichts und trifft keine Handelsentscheidung.
"""

from __future__ import annotations

from application.api.application_api import ApplicationApi
from application.api.router import ApiRequest, ApiResponse, Route, Router

__all__ = ["ApplicationApi", "ApiRequest", "ApiResponse", "Route", "Router"]
