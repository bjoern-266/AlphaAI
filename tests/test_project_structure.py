"""Strukturtests: stellen sicher, dass das Fundament vollständig vorhanden ist."""

from __future__ import annotations

from core.paths import CONFIG_DIR, DOCS_DIR, KNOWLEDGE_DIR, PROJECT_ROOT, SETTINGS_FILE

EXPECTED_PACKAGES = [
    "core",
    "data",
    "providers",
    "scanner",
    "engines",
    "patterns",
    "strategies",
    "dashboard",
    "database",
    "models",
]

EXPECTED_DOCS = [
    "ARCHITECTURE.md",
    "PROJECT_STATUS.md",
    "ROADMAP.md",
    "CHANGELOG.md",
    "HANDOVER.md",
    "AI_CONTEXT.md",
    "DECISIONS.md",
]

EXPECTED_KNOWLEDGE = [
    "market_rules.md",
    "risk.md",
    "journal.md",
    "ideas.md",
    "strategy.md",
    "indicator_rules.toml",
    "pattern_rules.toml",
    "strategy_rules.toml",
]


def test_expected_packages_exist() -> None:
    for package in EXPECTED_PACKAGES:
        init_file = PROJECT_ROOT / package / "__init__.py"
        assert init_file.is_file(), f"Fehlendes Paket: {package}"


def test_settings_file_exists() -> None:
    assert SETTINGS_FILE.is_file()
    assert CONFIG_DIR.is_dir()


def test_documentation_complete() -> None:
    for doc in EXPECTED_DOCS:
        assert (DOCS_DIR / doc).is_file(), f"Fehlende Doku: {doc}"


def test_knowledge_base_complete() -> None:
    for entry in EXPECTED_KNOWLEDGE:
        assert (KNOWLEDGE_DIR / entry).is_file(), f"Fehlende Wissensdatei: {entry}"
