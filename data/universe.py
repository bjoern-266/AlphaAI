"""Handelsuniversen (Symbollisten je Markt).

Ein :class:`Universe` bündelt die Symbole eines Marktes samt Metadaten. Die
Definitionen werden aus ``config/universe.toml`` geladen – im Code stehen keine
Symbollisten. Yahoo-spezifische Börsenkürzel (``suffix``) werden beim Erzeugen
der vollständigen Symbole angehängt.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from core.exceptions import AlphaAIError
from core.paths import UNIVERSE_FILE


class UniverseError(AlphaAIError):
    """Wird ausgelöst, wenn Universen fehlen oder ungültig definiert sind."""


@dataclass(frozen=True, slots=True)
class Universe:
    """Ein Handelsuniversum.

    Attributes:
        key: Technischer Schlüssel (z. B. ``"dax"``).
        name: Anzeigename (z. B. ``"DAX"``).
        region: Regionskürzel (z. B. ``"DE"``, ``"US"``).
        suffix: An Yahoo-Symbole anzuhängendes Börsenkürzel (z. B. ``".DE"``).
        complete: Ob die Liste vollständig ist (sonst kuratierte Startliste).
        description: Kurzbeschreibung.
        base_symbols: Symbole ohne Börsenkürzel, wie in der TOML hinterlegt.
    """

    key: str
    name: str
    region: str
    suffix: str
    complete: bool
    description: str
    base_symbols: tuple[str, ...]

    @property
    def symbols(self) -> tuple[str, ...]:
        """Vollständige Yahoo-Symbole inkl. Börsenkürzel (``suffix``)."""
        if not self.suffix:
            return self.base_symbols
        return tuple(f"{symbol}{self.suffix}" for symbol in self.base_symbols)

    @property
    def size(self) -> int:
        """Anzahl der Symbole im Universum."""
        return len(self.base_symbols)


def load_universes(path: Path | None = None) -> dict[str, Universe]:
    """Lädt alle Universen aus der TOML-Datei.

    Args:
        path: Optionaler Pfad. Standard ist ``config/universe.toml``.

    Returns:
        Zuordnung Schlüssel -> :class:`Universe`.

    Raises:
        UniverseError: Wenn die Datei fehlt oder ungültig ist.
    """
    universe_path = path or UNIVERSE_FILE
    if not universe_path.is_file():
        raise UniverseError(f"Universum-Datei nicht gefunden: {universe_path}")

    try:
        with universe_path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as error:
        raise UniverseError(f"Universum-Datei ist kein gültiges TOML: {error}") from error

    raw_universes = data.get("universes")
    if not isinstance(raw_universes, dict) or not raw_universes:
        raise UniverseError("Es ist mindestens ein Universum unter [universes] erforderlich.")

    universes: dict[str, Universe] = {}
    for key, entry in raw_universes.items():
        universes[key] = _build_universe(key, entry)
    return universes


def _build_universe(key: str, entry: object) -> Universe:
    """Erzeugt ein :class:`Universe` aus einem TOML-Eintrag."""
    if not isinstance(entry, dict):
        raise UniverseError(f"Universum '{key}' ist ungültig definiert.")
    try:
        return Universe(
            key=key,
            name=str(entry["name"]),
            region=str(entry["region"]),
            suffix=str(entry.get("suffix", "")),
            complete=bool(entry["complete"]),
            description=str(entry.get("description", "")),
            base_symbols=tuple(str(symbol).strip().upper() for symbol in entry["symbols"]),
        )
    except KeyError as error:
        raise UniverseError(f"Universum '{key}': fehlendes Feld {error}.") from error


def get_universe(key: str, path: Path | None = None) -> Universe:
    """Lädt ein einzelnes Universum anhand seines Schlüssels.

    Args:
        key: Schlüssel des Universums (z. B. ``"dax"``).
        path: Optionaler Pfad zur TOML-Datei.

    Returns:
        Das gewünschte :class:`Universe`.

    Raises:
        UniverseError: Wenn der Schlüssel unbekannt ist.
    """
    universes = load_universes(path)
    normalized = key.strip().lower()
    if normalized not in universes:
        available = ", ".join(sorted(universes))
        raise UniverseError(f"Unbekanntes Universum '{key}'. Verfügbar: {available}.")
    return universes[normalized]
