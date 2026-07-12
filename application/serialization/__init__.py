"""Serialisierung bestehender Reports in JSON-fähige Datenstrukturen.

Die Serialisierung **liest** die vorhandenen (unveränderlichen) Report-Modelle
und wandelt sie strukturerhaltend in JSON-fähige Grundtypen um. Es findet
**keine** Berechnung, Ableitung oder Veränderung von Fachdaten statt.
"""

from __future__ import annotations

from application.serialization.serializer import (
    to_json_bytes,
    to_json_text,
    to_jsonable,
)

__all__ = ["to_jsonable", "to_json_bytes", "to_json_text"]
