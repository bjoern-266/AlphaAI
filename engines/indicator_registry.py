"""Registry der verfügbaren Indikatoren.

Die Registry ist die **einzige** Stelle, an der Indikatoren bekannt gemacht
werden. Neue Indikatoren werden ausschließlich hier registriert
(:meth:`IndicatorRegistry.register` bzw. Ergänzung in
:func:`build_default_registry`). Die Engine kennt nur die Registry, nicht die
einzelnen Indikatorklassen.
"""

from __future__ import annotations

from core.registry import Registry
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


class IndicatorRegistry(Registry[BaseIndicator]):
    """Verwaltet die verfügbaren Indikatoren nach Name.

    Erbt Registrierung/Abfrage von der generischen :class:`core.registry.Registry`;
    das öffentliche Interface (``register``/``get``/``__contains__``/``names``/
    ``len``) bleibt unverändert.
    """

    def __init__(self) -> None:
        super().__init__(label="Indikator")


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
