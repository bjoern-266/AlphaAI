"""Zusammenführung der API: Routing, Zugriffskontrolle und Caching.

Die :class:`ApplicationApi` ist die zentrale, framework-unabhängige Fassade der
REST-API. Sie prüft den Zugriff (aktuell nur lokal), beantwortet Anfragen über
den Router und beschleunigt Wiederholungen über einen revisionsgebundenen
Cache. Der Cache invalidiert sich **automatisch**, sobald ein neuer Report
gespeichert wurde (die Speicher-Revision ändert sich) – so wird nie ein
veralteter Stand ausgeliefert, aber unveränderte Anfragen sind schnell.
"""

from __future__ import annotations

from application.api.router import ApiRequest, ApiResponse, Router
from application.authentication import AuthContext, AuthPolicy, LocalOnlyPolicy
from application.exceptions import ApplicationError, AuthenticationError
from application.repositories import ReportStore
from application.responses import error_from_exception
from core.cache import Cache
from models.application import EndpointInfo


class ApplicationApi:
    """Framework-unabhängige Fassade der REST-API.

    Args:
        router: Der verdrahtete Router mit allen Endpunkten.
        store: Der Report-Speicher (liefert die Revision für den Cache).
        auth_policy: Zugriffsrichtlinie (Standard: nur lokaler Zugriff).
        cache: Optionaler Antwort-Cache. Standard: interner Cache mit 256 Plätzen.
        api_version: Aktive API-Version (für Fehler-Metadaten außerhalb des Routers).
    """

    def __init__(
        self,
        router: Router,
        store: ReportStore,
        *,
        auth_policy: AuthPolicy | None = None,
        cache: Cache[ApiResponse] | None = None,
        api_version: str = "v1",
    ) -> None:
        self._router = router
        self._store = store
        self._auth = auth_policy or LocalOnlyPolicy()
        self._cache: Cache[ApiResponse] = cache or Cache(capacity=256)
        self._api_version = api_version

    @property
    def router(self) -> Router:
        """Der zugrunde liegende Router."""
        return self._router

    def endpoints(self) -> tuple[EndpointInfo, ...]:
        """Gibt die Beschreibungen aller registrierten Endpunkte zurück."""
        return self._router.endpoints()

    def handle(self, request: ApiRequest) -> ApiResponse:
        """Beantwortet eine API-Anfrage (Zugriffsprüfung, Cache, Routing).

        Auch bei ungültigen Anfragen oder Fehlern liefert die Methode stets eine
        wohlgeformte Antwort – der Dienst bleibt stabil.
        """
        try:
            self._auth.authorize(AuthContext(client_host=request.client_host))
        except AuthenticationError as error:
            return self._error(error)
        except ApplicationError as error:  # pragma: no cover - defensive
            return self._error(error)

        key = self._cache_key(request)
        cached = self._cache.get(key)
        if cached is not None:
            return ApiResponse(status=cached.status, envelope=cached.envelope, cached=True)

        response = self._router.dispatch(request)
        if response.ok:
            self._cache.set(key, response)
        return response

    def cache_metrics(self) -> dict[str, int]:
        """Gibt Cache-Kennzahlen zurück (für Health/Diagnose, keine Fachdaten)."""
        return {
            "hits": self._cache.hits,
            "misses": self._cache.misses,
            "size": len(self._cache),
            "revision": self._store.revision,
        }

    def clear_cache(self) -> None:
        """Leert den Antwort-Cache (z. B. nach manuellem Eingriff)."""
        self._cache.clear()

    def _cache_key(self, request: ApiRequest) -> str:
        """Bildet einen Cache-Schlüssel inkl. Speicher-Revision (Auto-Invalidation)."""
        query = "&".join(f"{name}={value}" for name, value in sorted(request.query.items()))
        return f"{self._store.revision}|{request.method}|{request.path}|{query}"

    def _error(self, error: ApplicationError) -> ApiResponse:
        """Baut eine Fehlerantwort (für vor dem Routing auftretende Fehler)."""
        envelope = error_from_exception(error, api_version=self._api_version)
        return ApiResponse(status=error.status, envelope=envelope)


__all__ = ["ApplicationApi"]
