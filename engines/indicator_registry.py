"""Registry der verfügbaren Indikatoren.

Die Registry ist die **einzige** Stelle, an der Indikatoren bekannt gemacht
werden. Neue Indikatoren werden ausschließlich hier registriert
(:meth:`IndicatorRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Indikatorklassen.
"""

from __future__ import annotations

from indicators.adx import AdxIndicator
from indicators.atr import AtrIndicator
from indicators.base import BaseIndicator
from indicators.bollinger import BollingerIndicator
from indicators.ema import EmaIndicator
from indicators.macd import MacdIndicator
from indicators.obv import ObvIndicator
from indicators.relative_volume import RelativeVolumeIndicator
from indicators.rsi import RsiIndicator
from indicators.stochastic import StochasticIndicator
from indicators.volume_profile import VolumeProfileIndicator
from indicators.vwap import VwapIndicator


class IndicatorRegistry:
    """Verwaltet die verfügbaren Indikatoren nach Name."""

    def __init__(self) -> None:
        self._by_name: dict[str, BaseIndicator] = {}

    def register(self, indicator: BaseIndicator) -> None:
        """Registriert einen Indikator.

        Args:
            indicator: Die zu registrierende Indikatorinstanz.

        Raises:
            ValueError: Wenn bereits ein Indikator mit demselben Namen existiert.
        """
        if indicator.name in self._by_name:
            raise ValueError(f"Indikator '{indicator.name}' ist bereits registriert.")
        self._by_name[indicator.name] = indicator

    def get(self, name: str) -> BaseIndicator:
        """Gibt den Indikator mit dem Namen zurück.

        Raises:
            KeyError: Wenn kein Indikator mit diesem Namen registriert ist.
        """
        if name not in self._by_name:
            raise KeyError(f"Unbekannter Indikator '{name}'.")
        return self._by_name[name]

    def __contains__(self, name: str) -> bool:
        """Prüft, ob ein Indikatorname registriert ist."""
        return name in self._by_name

    def names(self) -> list[str]:
        """Gibt die registrierten Indikatornamen sortiert zurück."""
        return sorted(self._by_name)

    def __len__(self) -> int:
        """Anzahl registrierter Indikatoren."""
        return len(self._by_name)


def build_default_registry() -> IndicatorRegistry:
    """Erzeugt eine Registry mit allen Standard-Indikatoren.

    Returns:
        Eine :class:`IndicatorRegistry` mit den elf Standard-Indikatoren.
    """
    registry = IndicatorRegistry()
    for indicator in (
        EmaIndicator(),
        RsiIndicator(),
        AtrIndicator(),
        VwapIndicator(),
        MacdIndicator(),
        RelativeVolumeIndicator(),
        AdxIndicator(),
        BollingerIndicator(),
        StochasticIndicator(),
        ObvIndicator(),
        VolumeProfileIndicator(),
    ):
        registry.register(indicator)
    return registry
