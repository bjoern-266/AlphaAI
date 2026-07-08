"""Fabrik zum Zusammenbau eines :class:`MarketRepository`.

Diese Fabrik verdrahtet die Bestandteile der Data Layer anhand der
Konfiguration: Sie erzeugt den konfigurierten Provider, einen TTL-Cache mit den
konfigurierten Ablaufzeiten und einen Validator. So bleibt die
Objekt-Erzeugung (Composition Root) an einer Stelle gebündelt und der übrige
Code frei von Konstruktionsdetails (Dependency Injection).
"""

from __future__ import annotations

import time
from collections.abc import Callable

from core.config import Settings
from data.cache import TTLCache
from data.validator import MarketDataValidator
from providers.base_provider import BaseProvider
from providers.provider_factory import create_provider
from repositories.market_repository import MarketRepository


def build_repository(
    settings: Settings,
    provider: BaseProvider | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> MarketRepository:
    """Erzeugt ein voll verdrahtetes :class:`MarketRepository`.

    Args:
        settings: Geladene Projektkonfiguration.
        provider: Optionaler Provider. Wird keiner übergeben, erzeugt die
            Fabrik den in ``settings.data.default_provider`` konfigurierten
            Provider. Die Übergabemöglichkeit dient Tests und Erweiterungen.
        clock: Zeitquelle für den Cache (injizierbar für Tests).

    Returns:
        Ein einsatzbereites :class:`MarketRepository`.
    """
    used_provider = provider or create_provider(settings.data.default_provider)
    cache = TTLCache(config=settings.data.cache, clock=clock)
    validator = MarketDataValidator()
    return MarketRepository(provider=used_provider, cache=cache, validator=validator)
