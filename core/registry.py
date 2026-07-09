"""Generische Plugin-Registry.

:class:`Registry` bündelt die zuvor viermal (Indicator/Pattern/Strategy/Score)
duplizierte Registry-Logik an **einer** Stelle. Eine Registry ist die einzige
Erweiterungsstelle einer Plugin-Familie: Neue Elemente werden ausschließlich
hier bekannt gemacht; die zugehörige Engine kennt nur die Registry, nicht die
einzelnen Element-Klassen.

Registrierbare Elemente müssen ein ``name``-Attribut besitzen
(:class:`Named`). Die konkreten Registries erben von dieser Basis, legen den
Elementtyp und ein sprechendes Label fest und liefern eine
``build_default_registry()``-Funktion. Ihr öffentliches Verhalten
(``register``/``get``/``__contains__``/``names``/``len``) bleibt unverändert.
"""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar, runtime_checkable

from core.exceptions import DuplicateRegistrationError, UnknownComponentError


@runtime_checkable
class Named(Protocol):
    """Protokoll für registrierbare Elemente: besitzen einen eindeutigen Namen."""

    name: str


T = TypeVar("T", bound=Named)


class Registry(Generic[T]):
    """Verwaltet benannte Elemente einer Plugin-Familie.

    Args:
        label: Sprechende Bezeichnung der Elementart (nur für Fehlermeldungen,
            z. B. ``"Indikator"`` oder ``"Muster"``).
    """

    def __init__(self, label: str = "Element") -> None:
        self._label = label
        self._by_name: dict[str, T] = {}

    def register(self, item: T) -> None:
        """Registriert ein Element.

        Raises:
            DuplicateRegistrationError: Wenn bereits ein Element mit demselben
                Namen registriert ist.
        """
        if item.name in self._by_name:
            raise DuplicateRegistrationError(
                f"{self._label} '{item.name}' ist bereits registriert."
            )
        self._by_name[item.name] = item

    def get(self, name: str) -> T:
        """Gibt das Element mit dem Namen zurück.

        Raises:
            UnknownComponentError: Wenn kein Element mit diesem Namen existiert.
        """
        if name not in self._by_name:
            raise UnknownComponentError(f"Unbekannt: {self._label} '{name}'.")
        return self._by_name[name]

    def __contains__(self, name: str) -> bool:
        """Prüft, ob ein Name registriert ist."""
        return name in self._by_name

    def names(self) -> list[str]:
        """Gibt die registrierten Namen sortiert zurück."""
        return sorted(self._by_name)

    def __len__(self) -> int:
        """Anzahl registrierter Elemente."""
        return len(self._by_name)
