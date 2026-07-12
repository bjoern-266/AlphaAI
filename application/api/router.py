"""Framework-unabhängiges Routing und Request/Response der REST-API.

Dieser Router bildet HTTP-Methode und Pfad auf registrierte Handler ab. Er
kennt kein Web-Framework: Requests und Responses sind einfache, testbare
Datenobjekte. Pfad-Vorlagen unterstützen Platzhalter (z. B.
``/opportunities/{ticker}``); der Router extrahiert die Werte und übergibt sie
dem Handler.

Ein Handler liefert bereits JSON-fähige Nutzdaten zurück; der Router verpackt
sie in eine einheitliche :class:`~models.application.ApiEnvelope`. Fehler
(``ApplicationError``) werden in eine Fehler-Hülle mit passendem Statuscode
übersetzt – die API bleibt dadurch auch bei ungültigen Anfragen stabil.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from application.exceptions import ApplicationError, InvalidRequestError, ReportNotFoundError
from application.responses import error_from_exception, success_envelope
from application.serialization import to_json_bytes
from models.application import ApiEnvelope, EndpointInfo

# Ein Handler erhält den Request und liefert JSON-fähige Nutzdaten zurück.
Handler = Callable[["ApiRequest"], Any]


@dataclass(frozen=True, slots=True)
class ApiRequest:
    """Eine eingehende API-Anfrage (framework-unabhängig).

    Attributes:
        method: HTTP-Methode (Großbuchstaben, z. B. ``"GET"``).
        path: Angefragter Pfad relativ zum API-Präfix (z. B. ``"/opportunities"``).
        path_params: Aus der Pfad-Vorlage extrahierte Werte.
        query: Query-Parameter als Text (z. B. ``{"limit": "5"}``).
        client_host: Absender-Adresse (für die Zugriffskontrolle).
    """

    method: str = "GET"
    path: str = "/"
    path_params: dict[str, str] = field(default_factory=dict)
    query: dict[str, str] = field(default_factory=dict)
    client_host: str = ""

    def query_int(self, name: str, default: int) -> int:
        """Liest einen Query-Parameter als ganze Zahl.

        Raises:
            InvalidRequestError: Wenn der Wert keine ganze Zahl ist.
        """
        raw = self.query.get(name)
        if raw is None or raw == "":
            return default
        try:
            return int(raw)
        except (TypeError, ValueError) as error:
            raise InvalidRequestError(
                f"Parameter '{name}' muss eine ganze Zahl sein.", detail={name: raw}
            ) from error


@dataclass(frozen=True, slots=True)
class ApiResponse:
    """Eine API-Antwort (framework-unabhängig).

    Attributes:
        status: HTTP-Statuscode.
        envelope: Die einheitliche Antwort-Hülle.
        cached: Ob die Antwort aus dem Cache stammt (nur Diagnose).
    """

    status: int
    envelope: ApiEnvelope
    cached: bool = False

    @property
    def ok(self) -> bool:
        """``True`` bei erfolgreicher Antwort (2xx)."""
        return 200 <= self.status < 300

    def json_bytes(self) -> bytes:
        """Serialisiert die Hülle als kompakte UTF-8-JSON-Bytes."""
        return to_json_bytes(self.envelope)


@dataclass(frozen=True, slots=True)
class Route:
    """Eine registrierte Route der API.

    Attributes:
        method: HTTP-Methode (Großbuchstaben).
        template: Pfad-Vorlage mit optionalen ``{platzhaltern}``.
        handler: Der aufzurufende Handler.
        info: Beschreibung des Endpunkts (für ``/`` und Dokumentation).
    """

    method: str
    template: str
    handler: Handler
    info: EndpointInfo

    def match(self, method: str, path: str) -> dict[str, str] | None:
        """Prüft, ob die Route auf Methode und Pfad passt.

        Returns:
            Die extrahierten Pfad-Parameter, oder ``None`` bei Nichtübereinstimmung.
        """
        if method.upper() != self.method:
            return None
        return _match_path(self.template, path)


class Router:
    """Verwaltet Routen und bildet Anfragen auf Antworten ab.

    Args:
        api_version: Aktive API-Version (für die Antwort-Metadaten).
    """

    def __init__(self, api_version: str = "v1") -> None:
        self._api_version = api_version
        self._routes: list[Route] = []

    def add(self, route: Route) -> None:
        """Registriert eine Route."""
        self._routes.append(route)

    def routes(self) -> tuple[Route, ...]:
        """Gibt alle registrierten Routen zurück (Registrierungsreihenfolge)."""
        return tuple(self._routes)

    def endpoints(self) -> tuple[EndpointInfo, ...]:
        """Gibt die Beschreibungen aller registrierten Endpunkte zurück."""
        return tuple(route.info for route in self._routes)

    def dispatch(self, request: ApiRequest) -> ApiResponse:
        """Leitet eine Anfrage an den passenden Handler und baut die Antwort.

        Fehlt eine passende Route, wird ``404`` zurückgegeben; unpassende Methode
        auf sonst existierendem Pfad ergibt ``405``. Handler-Fehler werden in
        strukturierte Fehlerantworten übersetzt.
        """
        path_exists = False
        for route in self._routes:
            params = route.match(request.method, request.path)
            if params is not None:
                enriched = _with_params(request, params)
                return self._run(route, enriched)
            if _match_path(route.template, request.path) is not None:
                path_exists = True

        if path_exists:
            return self._error(
                InvalidRequestError(
                    f"Methode '{request.method}' ist für '{request.path}' nicht erlaubt.",
                    detail={"path": request.path, "method": request.method},
                ),
                status=405,
            )
        return self._error(
            ReportNotFoundError(
                f"Unbekannter Pfad: '{request.path}'.", detail={"path": request.path}
            ),
            status=404,
        )

    def _run(self, route: Route, request: ApiRequest) -> ApiResponse:
        """Ruft einen Handler auf und verpackt Ergebnis bzw. Fehler."""
        try:
            data = route.handler(request)
        except ApplicationError as error:
            return self._error(error, status=error.status)
        meta: dict[str, Any] = {"kind": route.info.report_kind} if route.info.report_kind else {}
        envelope = success_envelope(data, api_version=self._api_version, meta=meta)
        return ApiResponse(status=200, envelope=envelope)

    def _error(self, error: ApplicationError, *, status: int) -> ApiResponse:
        """Baut eine Fehlerantwort aus einem :class:`ApplicationError`."""
        envelope = error_from_exception(error, api_version=self._api_version)
        return ApiResponse(status=status, envelope=envelope)


def _with_params(request: ApiRequest, params: dict[str, str]) -> ApiRequest:
    """Kopiert den Request und ergänzt die extrahierten Pfad-Parameter."""
    from dataclasses import replace

    return replace(request, path_params=params)


def _split(path: str) -> list[str]:
    """Zerlegt einen Pfad in nicht-leere Segmente."""
    return [segment for segment in path.strip("/").split("/") if segment != ""]


def _match_path(template: str, path: str) -> dict[str, str] | None:
    """Gleicht einen Pfad gegen eine Vorlage ab und extrahiert Platzhalter."""
    template_parts = _split(template)
    path_parts = _split(path)
    if len(template_parts) != len(path_parts):
        return None
    params: dict[str, str] = {}
    for expected, actual in zip(template_parts, path_parts, strict=True):
        if expected.startswith("{") and expected.endswith("}"):
            params[expected[1:-1]] = actual
        elif expected != actual:
            return None
    return params


__all__ = ["ApiRequest", "ApiResponse", "Route", "Router", "Handler"]
