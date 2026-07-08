"""Abstrakte Basis für alle Marktdaten-Provider.

Ein Provider kapselt den Zugriff auf genau eine Datenquelle und liefert die
Daten im kanonischen Schema eines :class:`MarketResult` zurück. Durch die
gemeinsame Schnittstelle sind Provider austauschbar (Dependency Inversion):
Repository und Engine kennen nur diese Basisklasse, nicht die konkrete Quelle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.exceptions import AlphaAIError
from data.market_request import MarketRequest
from data.market_result import MarketResult


class ProviderError(AlphaAIError):
    """Basisfehler für Provider-bezogene Probleme."""


class ProviderNotImplementedError(ProviderError):
    """Wird ausgelöst, wenn ein vorbereiteter Provider (noch) keine Daten liefert."""


class BaseProvider(ABC):
    """Gemeinsame Schnittstelle aller Provider.

    Konkrete Provider implementieren :meth:`fetch` und geben ihren Namen über
    :attr:`name` zurück.
    """

    #: Eindeutiger, kleingeschriebener Provider-Name (z. B. ``"yahoo"``).
    name: str = "base"

    @abstractmethod
    def fetch(self, request: MarketRequest) -> MarketResult:
        """Lädt Marktdaten gemäß der Anfrage.

        Args:
            request: Die auszuführende Marktdatenanfrage.

        Returns:
            Ein :class:`MarketResult` im kanonischen Schema.

        Raises:
            ProviderError: Bei Problemen mit der Datenquelle.
        """
        raise NotImplementedError
