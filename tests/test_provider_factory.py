"""Tests für die Provider-Factory."""

from __future__ import annotations

import pytest

from providers.base_provider import ProviderError, ProviderNotImplementedError
from providers.provider_factory import (
    available_providers,
    create_provider,
    planned_providers,
)
from providers.yahoo_provider import YahooProvider


def test_create_yahoo_provider() -> None:
    provider = create_provider("yahoo")
    assert isinstance(provider, YahooProvider)
    assert provider.name == "yahoo"


def test_create_is_case_insensitive() -> None:
    assert isinstance(create_provider("  YAHOO "), YahooProvider)


def test_planned_provider_raises_not_implemented() -> None:
    for name in ("finnhub", "polygon", "alphavantage", "iex"):
        with pytest.raises(ProviderNotImplementedError):
            create_provider(name)


def test_unknown_provider_raises() -> None:
    with pytest.raises(ProviderError):
        create_provider("does_not_exist")


def test_registries_are_disjoint_and_populated() -> None:
    assert "yahoo" in available_providers()
    assert set(planned_providers()) == {"finnhub", "polygon", "alphavantage", "iex"}
    assert not set(available_providers()) & set(planned_providers())
