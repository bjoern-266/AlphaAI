"""Tests des framework-unabhängigen Routers (Sprint 17)."""

from __future__ import annotations

import json

from application.api.router import ApiRequest, ApiResponse, Route, Router
from application.exceptions import InvalidRequestError, ReportNotFoundError
from models.application import EndpointInfo


def _route(template: str, handler, method: str = "GET") -> Route:
    info = EndpointInfo(method=method, path=template, name=template.strip("/") or "root")
    return Route(method=method, template=template, handler=handler, info=info)


def _router(*routes: Route) -> Router:
    router = Router()
    for route in routes:
        router.add(route)
    return router


def test_request_defaults() -> None:
    request = ApiRequest()
    assert request.method == "GET"
    assert request.path == "/"


def test_query_int_default() -> None:
    assert ApiRequest(query={}).query_int("limit", 10) == 10


def test_query_int_parses() -> None:
    assert ApiRequest(query={"limit": "5"}).query_int("limit", 10) == 5


def test_query_int_empty_uses_default() -> None:
    assert ApiRequest(query={"limit": ""}).query_int("limit", 7) == 7


def test_query_int_invalid_raises() -> None:
    try:
        ApiRequest(query={"limit": "abc"}).query_int("limit", 10)
    except InvalidRequestError as error:
        assert error.detail["limit"] == "abc"
    else:  # pragma: no cover
        raise AssertionError("Erwartete InvalidRequestError")


def test_match_static_path() -> None:
    route = _route("/health", lambda r: {"ok": True})
    assert route.match("GET", "/health") == {}


def test_match_wrong_method() -> None:
    route = _route("/health", lambda r: {})
    assert route.match("POST", "/health") is None


def test_match_extracts_param() -> None:
    route = _route("/opportunities/{ticker}", lambda r: {})
    assert route.match("GET", "/opportunities/AAPL") == {"ticker": "AAPL"}


def test_match_different_length() -> None:
    route = _route("/opportunities/{ticker}", lambda r: {})
    assert route.match("GET", "/opportunities/AAPL/extra") is None


def test_match_trailing_slash_ignored() -> None:
    route = _route("/health", lambda r: {})
    assert route.match("GET", "/health/") == {}


def test_dispatch_success_wraps_envelope() -> None:
    router = _router(_route("/health", lambda r: {"ok": True}))
    response = router.dispatch(ApiRequest(path="/health"))
    assert response.status == 200
    assert response.envelope.ok is True
    assert response.envelope.data == {"ok": True}


def test_dispatch_passes_path_params() -> None:
    router = _router(_route("/x/{id}", lambda r: {"id": r.path_params["id"]}))
    response = router.dispatch(ApiRequest(path="/x/42"))
    assert response.envelope.data == {"id": "42"}


def test_dispatch_unknown_path_404() -> None:
    router = _router(_route("/health", lambda r: {}))
    response = router.dispatch(ApiRequest(path="/missing"))
    assert response.status == 404
    assert response.envelope.error.code == "not_found"


def test_dispatch_wrong_method_405() -> None:
    router = _router(_route("/health", lambda r: {}))
    response = router.dispatch(ApiRequest(method="POST", path="/health"))
    assert response.status == 405


def test_dispatch_handler_error_translated() -> None:
    def boom(request: ApiRequest) -> dict:
        raise ReportNotFoundError("nix", detail={"ticker": "ZZZ"})

    router = _router(_route("/x", boom))
    response = router.dispatch(ApiRequest(path="/x"))
    assert response.status == 404
    assert response.envelope.error.detail == {"ticker": "ZZZ"}


def test_static_route_wins_over_param_route() -> None:
    router = _router(
        _route("/opportunities/top", lambda r: {"kind": "top"}),
        _route("/opportunities/{ticker}", lambda r: {"kind": "ticker"}),
    )
    top = router.dispatch(ApiRequest(path="/opportunities/top"))
    ticker = router.dispatch(ApiRequest(path="/opportunities/AAPL"))
    assert top.envelope.data == {"kind": "top"}
    assert ticker.envelope.data == {"kind": "ticker"}


def test_meta_kind_included() -> None:
    info = EndpointInfo(method="GET", path="/x", name="x", report_kind="operations")
    router = _router(Route(method="GET", template="/x", handler=lambda r: {}, info=info))
    response = router.dispatch(ApiRequest(path="/x"))
    assert response.envelope.meta["kind"] == "operations"


def test_endpoints_listed() -> None:
    router = _router(_route("/a", lambda r: {}), _route("/b", lambda r: {}))
    assert len(router.endpoints()) == 2


def test_routes_order_preserved() -> None:
    router = _router(_route("/a", lambda r: {}), _route("/b", lambda r: {}))
    assert [r.template for r in router.routes()] == ["/a", "/b"]


def test_response_json_bytes_valid() -> None:
    router = _router(_route("/health", lambda r: {"ok": True}))
    response = router.dispatch(ApiRequest(path="/health"))
    parsed = json.loads(response.json_bytes())
    assert parsed["ok"] is True
    assert parsed["data"] == {"ok": True}


def test_response_ok_property() -> None:
    ok = ApiResponse(status=200, envelope=router_envelope())
    err = ApiResponse(status=404, envelope=router_envelope())
    assert ok.ok is True
    assert err.ok is False


def router_envelope():
    """Kleine Hilfe: liefert eine minimale Erfolgs-Hülle."""
    from application.responses import success_envelope

    return success_envelope({})


def test_root_path_matches_slash() -> None:
    router = _router(_route("/", lambda r: {"root": True}))
    response = router.dispatch(ApiRequest(path="/"))
    assert response.envelope.data == {"root": True}
