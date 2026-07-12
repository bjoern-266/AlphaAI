"""Generischer, verlustfreier JSON-Serialisierer für Report-Modelle.

Der Serialisierer wandelt beliebige AlphaAI-Report-Objekte (frozen Dataclasses,
Enums, Zeitstempel, Tupel, Mappings) rekursiv in JSON-fähige Grundtypen
(``dict``/``list``/``str``/``int``/``float``/``bool``/``None``) um.

Bewusste Entscheidung: eine **einzige**, allgemeine Umwandlung statt vieler
handgeschriebener ``to_dict``-Methoden. Das hält die Serialisierung frei von
Fachwissen (kein Bezug zu einzelnen Report-Feldern) und damit stabil, wenn neue
Report-Felder hinzukommen. NaN/Infinity werden zu ``None``, da Standard-JSON
diese nicht kennt (keine Verfälschung, nur zulässige Darstellung).
"""

from __future__ import annotations

import dataclasses
import json
import math
from datetime import date, datetime
from enum import Enum
from typing import Any

_JSON_PRIMITIVES = (str, bool, int)


def to_jsonable(value: Any) -> Any:
    """Wandelt ein beliebiges Objekt rekursiv in JSON-fähige Grundtypen um.

    Unterstützte Eingaben:

    * ``None``/``str``/``bool``/``int`` – unverändert übernommen,
    * ``float`` – NaN/Infinity werden zu ``None`` (Standard-JSON-konform),
    * ``Enum`` – dessen ``value``,
    * ``datetime``/``date`` – ISO-8601-Text,
    * frozen/normale Dataclass – ``dict`` ihrer Felder,
    * ``Mapping`` – ``dict`` mit textuellen Schlüsseln,
    * ``list``/``tuple``/``set`` – ``list`` der umgewandelten Elemente,
    * alles Übrige – ``str(value)`` als sichere Rückfallebene.

    Args:
        value: Das umzuwandelnde Objekt (typischerweise ein Report).

    Returns:
        Eine ausschließlich aus JSON-Grundtypen bestehende Struktur.
    """
    if value is None:
        return None
    if isinstance(value, _JSON_PRIMITIVES):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Enum):
        return to_jsonable(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {name: to_jsonable(item) for name, item in _dataclass_items(value)}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _dataclass_items(value: Any) -> list[tuple[str, Any]]:
    """Liest die Felder einer Dataclass als (Name, Wert)-Paare (ohne Umwandlung)."""
    return [(f.name, getattr(value, f.name)) for f in dataclasses.fields(value)]


def to_json_text(value: Any, *, indent: int | None = None) -> str:
    """Serialisiert ein Objekt als kompakten (oder eingerückten) JSON-Text.

    Args:
        value: Das umzuwandelnde Objekt.
        indent: Einrückung für lesbare Ausgabe; ``None`` erzeugt kompaktes JSON.

    Returns:
        Ein JSON-Dokument als Text (UTF-8, ohne ASCII-Escapes).
    """
    separators = (",", ":") if indent is None else None
    return json.dumps(
        to_jsonable(value),
        ensure_ascii=False,
        indent=indent,
        separators=separators,
        sort_keys=False,
    )


def to_json_bytes(value: Any) -> bytes:
    """Serialisiert ein Objekt als kompakte UTF-8-JSON-Bytes (für HTTP-Antworten)."""
    return to_json_text(value).encode("utf-8")


__all__ = ["to_jsonable", "to_json_text", "to_json_bytes"]
