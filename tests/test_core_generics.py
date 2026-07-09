"""Tests für die generische Cache-/Registry-Basis und die Exception-Hierarchie."""

from __future__ import annotations

import pytest

from core.cache import Cache
from core.exceptions import (
    AlphaAIError,
    CacheCapacityError,
    DuplicateRegistrationError,
    IndicatorParameterError,
    ParameterError,
    RegistryError,
    UnknownComponentError,
)
from core.registry import Registry


class _Item:
    def __init__(self, name: str) -> None:
        self.name = name


def test_generic_cache_fifo_and_counting() -> None:
    cache: Cache[int] = Cache(capacity=2)
    assert cache.get("a") is None
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # verdrängt "a"
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert len(cache) == 2
    assert cache.hits == 1
    assert cache.misses == 2


def test_generic_cache_capacity_must_be_positive() -> None:
    with pytest.raises(CacheCapacityError):
        Cache(capacity=0)


def test_generic_registry_register_get_and_errors() -> None:
    registry: Registry[_Item] = Registry(label="Test")
    item = _Item("x")
    registry.register(item)
    assert "x" in registry
    assert registry.get("x") is item
    assert registry.names() == ["x"]
    assert len(registry) == 1
    with pytest.raises(DuplicateRegistrationError):
        registry.register(_Item("x"))
    with pytest.raises(UnknownComponentError):
        registry.get("missing")


def test_exception_hierarchy_roots() -> None:
    # Parameterfehler sind AlphaAIError und – rückwärtskompatibel – ValueError.
    assert issubclass(IndicatorParameterError, ParameterError)
    assert issubclass(ParameterError, AlphaAIError)
    assert issubclass(IndicatorParameterError, ValueError)
    # Registry-Fehler sind AlphaAIError; Duplikat zusätzlich ValueError,
    # Unbekannt zusätzlich KeyError.
    assert issubclass(RegistryError, AlphaAIError)
    assert issubclass(DuplicateRegistrationError, ValueError)
    assert issubclass(UnknownComponentError, KeyError)
    assert issubclass(CacheCapacityError, ValueError)
