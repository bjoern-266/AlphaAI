"""Architektur-Qualität als automatischer Test (Sprint 7.5).

Hängt den Qualitäts-Check (Zyklenfreiheit, Plugin-Unabhängigkeit, SOLID,
saubere Entities-Schicht) fest in die Testsuite ein, damit
Architekturverletzungen sofort auffallen.
"""

from __future__ import annotations

import pytest

from scripts.quality_check import run_checks

RESULTS = run_checks()


@pytest.mark.parametrize("check", sorted(RESULTS))
def test_no_architecture_violations(check: str) -> None:
    problems = RESULTS[check]
    assert problems == [], f"{check}: {problems}"
