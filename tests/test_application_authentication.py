"""Tests der vorbereiteten Zugriffskontrolle (Sprint 17)."""

from __future__ import annotations

import pytest

from application.authentication import AuthContext, LocalOnlyPolicy, OpenPolicy
from application.exceptions import AuthenticationError


def test_local_only_allows_loopback_ipv4() -> None:
    LocalOnlyPolicy().authorize(AuthContext(client_host="127.0.0.1"))


def test_local_only_allows_loopback_ipv6() -> None:
    LocalOnlyPolicy().authorize(AuthContext(client_host="::1"))


def test_local_only_allows_localhost() -> None:
    LocalOnlyPolicy().authorize(AuthContext(client_host="localhost"))


def test_local_only_allows_empty_host() -> None:
    LocalOnlyPolicy().authorize(AuthContext(client_host=""))


def test_local_only_rejects_remote() -> None:
    with pytest.raises(AuthenticationError):
        LocalOnlyPolicy().authorize(AuthContext(client_host="10.0.0.5"))


def test_local_only_case_insensitive() -> None:
    LocalOnlyPolicy().authorize(AuthContext(client_host="LOCALHOST"))


def test_local_only_extra_hosts() -> None:
    policy = LocalOnlyPolicy(allowed_hosts=frozenset({"192.168.1.10"}))
    policy.authorize(AuthContext(client_host="192.168.1.10"))


def test_local_only_extra_hosts_still_rejects_others() -> None:
    policy = LocalOnlyPolicy(allowed_hosts=frozenset({"192.168.1.10"}))
    with pytest.raises(AuthenticationError):
        policy.authorize(AuthContext(client_host="192.168.1.11"))


def test_rejection_detail_contains_host() -> None:
    try:
        LocalOnlyPolicy().authorize(AuthContext(client_host="8.8.8.8"))
    except AuthenticationError as error:
        assert error.detail["client_host"] == "8.8.8.8"
        assert error.status == 401
    else:  # pragma: no cover
        raise AssertionError("Erwartete AuthenticationError")


def test_open_policy_allows_any() -> None:
    OpenPolicy().authorize(AuthContext(client_host="8.8.8.8"))


def test_policy_names() -> None:
    assert LocalOnlyPolicy().name == "local_only"
    assert OpenPolicy().name == "open"


def test_auth_context_defaults() -> None:
    context = AuthContext()
    assert context.client_host == ""
    assert context.token == ""
    assert context.headers == {}
