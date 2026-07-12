"""Definition aller API-Endpunkte (reine Verdrahtung, keine Fachlogik).

Diese Datei verbindet die stabilen URL-Pfade mit den Lesediensten. Jeder
Handler liest ausschließlich vorhandene Reports über die Dienste und liefert
JSON-fähige Nutzdaten zurück – es wird **nichts** berechnet.

Die Endpunkt-Gruppen entsprechen der Vorgabe:

* System: ``/health``, ``/status``, ``/version``, ``/scheduler``, ``/operations``
* Märkte: ``/markets``, ``/market-status``, ``/opportunities``,
  ``/opportunities/top``, ``/opportunities/{ticker}``, ``/discovery``
* Empfehlungen: ``/recommendations``, ``/recommendations/{ticker}``
* Analytics: ``/analytics``, ``/backtesting``, ``/paper-trading``
* Dashboard: ``/dashboard``
"""

from __future__ import annotations

from application.api.router import ApiRequest, Handler, Route, Router
from application.health import HealthMonitor
from application.serialization import to_jsonable
from application.services import ReportService, SystemService
from models.application import EndpointInfo, ReportKind

# Standardanzahl der Top-Chancen, falls kein ``limit`` übergeben wird.
_DEFAULT_TOP_LIMIT = 10


def build_router(
    reports: ReportService,
    system: SystemService,
    health: HealthMonitor,
    *,
    api_version: str = "v1",
) -> Router:
    """Baut den vollständig verdrahteten :class:`Router` der API.

    Args:
        reports: Lesedienst für gespeicherte Reports.
        system: Systemdienst (Version/Status).
        health: Health-Monitor (aggregierter Zustand).
        api_version: Aktive API-Version (für die Antwort-Metadaten).

    Returns:
        Ein Router mit allen registrierten Endpunkten.
    """
    router = Router(api_version=api_version)

    def get(path: str, name: str, description: str, handler: Handler, kind: str = "") -> None:
        """Registriert einen GET-Endpunkt."""
        info = EndpointInfo(
            method="GET", path=path, name=name, description=description, report_kind=kind
        )
        router.add(Route(method="GET", template=path, handler=handler, info=info))

    # ---------------------------------------------------------------- System
    get(
        "/health",
        "health",
        "Aggregierter Gesundheitszustand des Backends.",
        lambda request: to_jsonable(health.report()),
    )
    get(
        "/status",
        "status",
        "Kompakte Statuszusammenfassung des Dienstes.",
        lambda request: system.status(),
    )
    get(
        "/version",
        "version",
        "Version und Beschreibung des Backend-Dienstes.",
        lambda request: system.version(),
    )
    get(
        "/scheduler",
        "scheduler",
        "Zustand des Schedulers (nächster/laufender Scan, Historie).",
        lambda request: reports.scheduler(),
        kind=ReportKind.OPERATIONS.value,
    )
    get(
        "/operations",
        "operations",
        "Vollständiger Operations-Report der Live Operations Platform.",
        lambda request: reports.operations(),
        kind=ReportKind.OPERATIONS.value,
    )

    # ---------------------------------------------------------------- Märkte
    get(
        "/markets",
        "markets",
        "Zustände aller beobachteten Märkte (offen/geschlossen).",
        lambda request: reports.markets(),
        kind=ReportKind.OPERATIONS.value,
    )
    get(
        "/market-status",
        "market_status",
        "Zusammengefasste Marktuhr (offene Märkte, nächste Öffnung).",
        lambda request: reports.market_status(),
        kind=ReportKind.OPERATIONS.value,
    )
    get(
        "/opportunities",
        "opportunities",
        "Vollständiger Opportunity-Report (Market Intelligence).",
        lambda request: reports.opportunities(),
        kind=ReportKind.OPPORTUNITIES.value,
    )
    get(
        "/opportunities/top",
        "opportunities_top",
        "Die besten Chancen nach Ranking (Parameter 'limit').",
        _top_opportunities(reports),
        kind=ReportKind.OPPORTUNITIES.value,
    )
    get(
        "/opportunities/{ticker}",
        "opportunity_by_ticker",
        "Chance zu einem einzelnen Ticker.",
        lambda request: reports.opportunity(request.path_params["ticker"]),
        kind=ReportKind.OPPORTUNITIES.value,
    )
    get(
        "/discovery",
        "discovery",
        "Vollständiger Market-Discovery-Report.",
        lambda request: reports.discovery(),
        kind=ReportKind.DISCOVERY.value,
    )

    # ---------------------------------------------------------- Empfehlungen
    get(
        "/recommendations",
        "recommendations",
        "Vollständiger Recommendation-Report.",
        lambda request: reports.recommendations(),
        kind=ReportKind.RECOMMENDATIONS.value,
    )
    get(
        "/recommendations/{ticker}",
        "recommendation_by_ticker",
        "Empfehlung zu einem einzelnen Ticker.",
        lambda request: reports.recommendation(request.path_params["ticker"]),
        kind=ReportKind.RECOMMENDATIONS.value,
    )

    # ------------------------------------------------------------- Analytics
    get(
        "/analytics",
        "analytics",
        "Vollständiger Analytics-Report.",
        lambda request: reports.analytics(),
        kind=ReportKind.ANALYTICS.value,
    )
    get(
        "/backtesting",
        "backtesting",
        "Vollständiger Backtesting-Report.",
        lambda request: reports.backtesting(),
        kind=ReportKind.BACKTESTING.value,
    )
    get(
        "/paper-trading",
        "paper_trading",
        "Vollständiger Paper-Trading-Report.",
        lambda request: reports.paper_trading(),
        kind=ReportKind.PAPER_TRADING.value,
    )

    # ------------------------------------------------------------- Dashboard
    get(
        "/dashboard",
        "dashboard",
        "Zusammengesetzter Schnappschuss aller Reports (dieselbe Quelle wie die App).",
        lambda request: reports.dashboard(),
        kind=ReportKind.DASHBOARD.value,
    )

    return router


def _top_opportunities(reports: ReportService) -> Handler:
    """Baut den Handler für ``/opportunities/top`` (liest 'limit' aus der Query)."""

    def handler(request: ApiRequest) -> list:
        limit = request.query_int("limit", _DEFAULT_TOP_LIMIT)
        return reports.top_opportunities(limit)

    return handler


__all__ = ["build_router"]
