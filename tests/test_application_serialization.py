"""Tests des generischen JSON-Serialisierers (Sprint 17)."""

from __future__ import annotations

import dataclasses
import json
import math
from datetime import UTC, date, datetime
from enum import Enum

from application.serialization import to_json_bytes, to_json_text, to_jsonable
from models.application import HealthStatus, ServiceInfo
from models.operations import Heartbeat


class _Color(Enum):
    RED = "red"
    ONE = 1


@dataclasses.dataclass(frozen=True)
class _Nested:
    name: str
    value: int


@dataclasses.dataclass(frozen=True)
class _Outer:
    nested: _Nested
    items: tuple[int, ...]
    when: datetime


def test_primitives_pass_through() -> None:
    assert to_jsonable("x") == "x"
    assert to_jsonable(5) == 5
    assert to_jsonable(True) is True
    assert to_jsonable(None) is None


def test_float_finite_kept() -> None:
    assert to_jsonable(1.5) == 1.5


def test_float_nan_becomes_none() -> None:
    assert to_jsonable(math.nan) is None


def test_float_infinity_becomes_none() -> None:
    assert to_jsonable(math.inf) is None
    assert to_jsonable(-math.inf) is None


def test_enum_uses_value() -> None:
    assert to_jsonable(_Color.RED) == "red"
    assert to_jsonable(_Color.ONE) == 1


def test_health_status_enum_serialized() -> None:
    assert to_jsonable(HealthStatus.OK) == "ok"


def test_datetime_iso() -> None:
    assert to_jsonable(datetime(2026, 7, 12, 14, 30, tzinfo=UTC)) == "2026-07-12T14:30:00+00:00"


def test_date_iso() -> None:
    assert to_jsonable(date(2026, 7, 12)) == "2026-07-12"


def test_dataclass_becomes_dict() -> None:
    result = to_jsonable(_Nested(name="a", value=1))
    assert result == {"name": "a", "value": 1}


def test_nested_dataclass_recursion() -> None:
    outer = _Outer(_Nested("a", 1), (1, 2, 3), datetime(2026, 1, 1, tzinfo=UTC))
    result = to_jsonable(outer)
    assert result["nested"] == {"name": "a", "value": 1}
    assert result["items"] == [1, 2, 3]
    assert result["when"].startswith("2026-01-01")


def test_tuple_becomes_list() -> None:
    assert to_jsonable((1, 2)) == [1, 2]


def test_set_becomes_list() -> None:
    assert sorted(to_jsonable({1, 2, 3})) == [1, 2, 3]


def test_dict_keys_stringified() -> None:
    assert to_jsonable({1: "a"}) == {"1": "a"}


def test_bytes_decoded() -> None:
    assert to_jsonable(b"hello") == "hello"


def test_unknown_object_falls_back_to_str() -> None:
    class Weird:
        def __str__(self) -> str:
            return "weird"

    assert to_jsonable(Weird()) == "weird"


def test_real_frozen_model_serialized() -> None:
    info = ServiceInfo(name="AlphaAI", started_at=datetime(2026, 1, 1, tzinfo=UTC))
    result = to_jsonable(info)
    assert result["name"] == "AlphaAI"
    assert result["started_at"].startswith("2026-01-01")


def test_operations_model_serialized() -> None:
    beat = Heartbeat(alive=True, age_seconds=5, interval_seconds=60)
    result = to_jsonable(beat)
    assert result["alive"] is True
    assert result["age_seconds"] == 5


def test_to_json_text_is_valid_json() -> None:
    text = to_json_text({"a": [1, 2], "b": "x"})
    assert json.loads(text) == {"a": [1, 2], "b": "x"}


def test_to_json_text_compact() -> None:
    text = to_json_text({"a": 1, "b": 2})
    assert " " not in text


def test_to_json_text_indent() -> None:
    text = to_json_text({"a": 1}, indent=2)
    assert "\n" in text


def test_to_json_text_unicode_preserved() -> None:
    text = to_json_text({"name": "Zürich"})
    assert "Zürich" in text


def test_to_json_bytes_roundtrip() -> None:
    payload = {"ticker": "AAPL", "score": 82.5}
    raw = to_json_bytes(payload)
    assert isinstance(raw, bytes)
    assert json.loads(raw.decode("utf-8")) == payload


def test_none_field_kept() -> None:
    info = ServiceInfo()
    result = to_jsonable(info)
    assert result["started_at"] is None


def test_list_of_dataclasses() -> None:
    items = [_Nested("a", 1), _Nested("b", 2)]
    assert to_jsonable(items) == [{"name": "a", "value": 1}, {"name": "b", "value": 2}]
