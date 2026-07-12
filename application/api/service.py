"""Dünner FastAPI-/uvicorn-Adapter für die REST-API.

Dieser Adapter bindet die framework-unabhängige :class:`ApplicationApi` an
FastAPI an. FastAPI/uvicorn werden **erst hier und nur bei Bedarf** importiert,
damit der API-Kern (und die gesamte Testsuite) ohne diese optionalen
Abhängigkeiten lauffähig bleibt – dieselbe Trennung wie beim streamlit-freien
Dashboard.

Der Adapter enthält **keinerlei Fachlogik**: Er übersetzt lediglich HTTP nach
:class:`ApiRequest`, ruft ``ApplicationApi.handle`` auf und schreibt die
JSON-Hülle samt Statuscode zurück. Er unterstützt GZip-Kompression großer
Antworten (falls der Client sie akzeptiert).
"""

from __future__ import annotations

from typing import Any

from application.api.application_api import ApplicationApi
from application.api.router import ApiRequest

# Ab dieser Antwortgröße (Bytes) wird GZip-Kompression aktiviert.
_GZIP_MIN_BYTES = 1024


def create_fastapi_app(api: ApplicationApi, *, api_prefix: str = "/api/v1") -> Any:
    """Baut eine FastAPI-App, die alle Endpunkte der :class:`ApplicationApi` bedient.

    Args:
        api: Die framework-unabhängige API-Fassade.
        api_prefix: Gemeinsames URL-Präfix aller Endpunkte (Versionierung).

    Returns:
        Eine konfigurierte ``fastapi.FastAPI``-Instanz.

    Raises:
        RuntimeError: Wenn FastAPI nicht installiert ist.
    """
    try:
        from fastapi import FastAPI, Request
        from fastapi.middleware.gzip import GZipMiddleware
        from fastapi.responses import Response
    except ModuleNotFoundError as error:  # pragma: no cover - optionale Abhängigkeit
        raise RuntimeError(
            "FastAPI ist nicht installiert. Installieren Sie 'fastapi' und 'uvicorn', "
            "um die REST-API zu betreiben."
        ) from error

    app = FastAPI(
        title="AlphaAI Backend API",
        version=api._api_version,  # noqa: SLF001 - bewusster, kontrollierter Zugriff
        description="Stellt ausschließlich vorhandene AlphaAI-Reports als JSON bereit.",
    )
    app.add_middleware(GZipMiddleware, minimum_size=_GZIP_MIN_BYTES)

    async def endpoint(request: Request) -> Response:
        """Übersetzt eine HTTP-Anfrage in einen :class:`ApiRequest` und antwortet."""
        api_request = ApiRequest(
            method=request.method,
            path=request.url.path[len(api_prefix) :] or "/",
            query={key: value for key, value in request.query_params.items()},
            client_host=request.client.host if request.client is not None else "",
        )
        result = api.handle(api_request)
        return Response(
            content=result.json_bytes(),
            status_code=result.status,
            media_type="application/json",
        )

    for route in api.router.routes():
        app.add_api_route(
            f"{api_prefix}{route.template}",
            endpoint,
            methods=[route.method],
            name=route.info.name,
            summary=route.info.description,
        )
    return app


__all__ = ["create_fastapi_app"]
