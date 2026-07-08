"""Tests für die Universen (Laden aus TOML)."""

from __future__ import annotations

from pathlib import Path

import pytest

from data.universe import UniverseError, get_universe, load_universes

SAMPLE = """
[universes.dax]
name = "DAX"
region = "DE"
suffix = ".DE"
complete = true
description = "Test"
symbols = ["sap", "bmw"]

[universes.us]
name = "US"
region = "US"
suffix = ""
complete = false
description = "Test"
symbols = ["AAPL"]
"""


def _write(tmp_path: Path, content: str) -> Path:
    target = tmp_path / "universe.toml"
    target.write_text(content, encoding="utf-8")
    return target


def test_load_universes(tmp_path: Path) -> None:
    universes = load_universes(_write(tmp_path, SAMPLE))
    assert set(universes) == {"dax", "us"}


def test_symbols_get_suffix_and_uppercase(tmp_path: Path) -> None:
    universe = get_universe("dax", _write(tmp_path, SAMPLE))
    assert universe.symbols == ("SAP.DE", "BMW.DE")
    assert universe.size == 2


def test_symbols_without_suffix(tmp_path: Path) -> None:
    universe = get_universe("us", _write(tmp_path, SAMPLE))
    assert universe.symbols == ("AAPL",)


def test_unknown_universe_raises(tmp_path: Path) -> None:
    with pytest.raises(UniverseError, match="Unbekanntes Universum"):
        get_universe("mdax", _write(tmp_path, SAMPLE))


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(UniverseError, match="nicht gefunden"):
        load_universes(tmp_path / "missing.toml")


def test_shipped_universe_file_is_valid() -> None:
    """Die mitgelieferte config/universe.toml muss ladbar sein."""
    universes = load_universes()
    assert "dax" in universes
    assert universes["dax"].complete is True
    assert universes["dax"].size == 40
