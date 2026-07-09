"""Zentrale Projektpfade.

Alle Verzeichnis- und Dateipfade werden an genau einer Stelle abgeleitet.
Dadurch gibt es im restlichen Code keine hartcodierten Pfade und das
Projekt bleibt unabhängig vom aktuellen Arbeitsverzeichnis lauffähig.
"""

from __future__ import annotations

from pathlib import Path

# Wurzelverzeichnis des Projekts (Ordner ``AlphaAI/``).
# ``paths.py`` liegt in ``AlphaAI/core/``, daher zeigt ``parents[1]`` auf die
# Projektwurzel.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

CONFIG_DIR: Path = PROJECT_ROOT / "config"
KNOWLEDGE_DIR: Path = PROJECT_ROOT / "knowledge"
DOCS_DIR: Path = PROJECT_ROOT / "docs"
LOGS_DIR: Path = PROJECT_ROOT / "logs"
OUTPUT_DIR: Path = PROJECT_ROOT / "output"
DATABASE_DIR: Path = PROJECT_ROOT / "database"

# Standard-Dateipfade.
SETTINGS_FILE: Path = CONFIG_DIR / "settings.toml"
UNIVERSE_FILE: Path = CONFIG_DIR / "universe.toml"
INDICATOR_RULES_FILE: Path = KNOWLEDGE_DIR / "indicator_rules.toml"
PATTERN_RULES_FILE: Path = KNOWLEDGE_DIR / "pattern_rules.toml"
STRATEGY_RULES_FILE: Path = KNOWLEDGE_DIR / "strategy_rules.toml"
SCORE_RULES_FILE: Path = KNOWLEDGE_DIR / "score_rules.toml"
RISK_RULES_FILE: Path = KNOWLEDGE_DIR / "risk_rules.toml"
LOG_FILE: Path = LOGS_DIR / "alpha_ai.log"


def ensure_runtime_dirs() -> None:
    """Legt zur Laufzeit benötigte Verzeichnisse an, falls sie fehlen.

    ``logs`` und ``output`` werden bewusst nicht mit Inhalten versioniert.
    Diese Funktion stellt sicher, dass sie vor dem ersten Schreibzugriff
    existieren.
    """
    for directory in (LOGS_DIR, OUTPUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
