"""Automatische Architektur-Qualitätsprüfung.

Prüft statisch (per AST, ohne Import der Module):

* **Import-Zyklen** über alle internen Pakete,
* **Unabhängigkeit** der Plugin-Familien (Indikatoren/Muster/Strategien/Scores):
  kein Plugin importiert ein Geschwister-Plugin (nur ``base``) oder ``engines``,
* eine einfache **SOLID-Heuristik** (je Plugin-Datei genau eine Basisklassen-
  Implementierung mit den geforderten Methoden),
* **Clean Architecture**: die Entities-Schicht ``models`` importiert nichts aus
  höheren Schichten (Engines, Data, Provider, Scanner, Dashboard).

Rückgabe/Exit-Code: 0 = bestanden, 1 = Verstöße gefunden. Die Funktion
:func:`run_checks` liefert die Verstöße strukturiert zurück und wird von der
Testsuite (``tests/test_quality.py``) aufgerufen.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Interne Pakete (Reihenfolge = grobe Schichtung von unten nach oben).
PACKAGES = [
    "core",
    "models",
    "data",
    "providers",
    "repositories",
    "scanner",
    "engines",
    "indicators",
    "patterns",
    "strategies",
    "scores",
    "risk",
    "recommendation",
    "pipeline",
    "backtesting",
    "paper_trading",
    "analytics",
    "market_intelligence",
    "market_discovery",
    "dashboard",
]

# Schichten oberhalb der Entities: ``models`` darf daraus nichts importieren.
HIGHER_LAYERS = ("engines", "data", "providers", "repositories", "scanner", "dashboard")


def module_name(path: Path) -> str:
    """Bildet einen Dateipfad auf den Modulnamen ab (z. B. ``core.cache``)."""
    return ".".join(path.relative_to(ROOT).with_suffix("").parts)


def internal_imports(path: Path) -> set[str]:
    """Sammelt alle Importe eines Moduls, die auf interne Pakete zeigen."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in PACKAGES:
                found.add(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in PACKAGES:
                    found.add(alias.name)
    return found


def build_graph() -> dict[str, set[str]]:
    """Baut den Import-Graphen über alle internen Module."""
    graph: dict[str, set[str]] = {}
    for package in PACKAGES:
        for path in (ROOT / package).rglob("*.py"):
            graph[module_name(path)] = internal_imports(path)
    return graph


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Findet Import-Zyklen im Graphen (Tiefensuche)."""
    cycles: list[list[str]] = []
    visited: set[str] = set()

    def dfs(node: str, stack: list[str]) -> None:
        if node in stack:
            cycles.append(stack[stack.index(node) :] + [node])
            return
        if node in visited or node not in graph:
            return
        stack.append(node)
        for dep in graph[node]:
            dfs(dep, stack)
        stack.pop()
        visited.add(node)

    for start in graph:
        dfs(start, [])
    return cycles


def check_independence(package: str) -> list[str]:
    """Kein Plugin-Modul importiert ein Geschwister-Modul (außer ``base``) oder ``engines``."""
    problems: list[str] = []
    for path in (ROOT / package).glob("*.py"):
        if path.name in {"__init__.py", "base.py"}:
            continue
        for imp in internal_imports(path):
            if imp.startswith(f"{package}.") and imp != f"{package}.base":
                problems.append(f"{package}/{path.name}: importiert '{imp}'")
            if imp.startswith("engines."):
                problems.append(f"{package}/{path.name}: importiert aus engines ('{imp}')")
    return problems


def check_models_layer() -> list[str]:
    """Die Entities-Schicht ``models`` darf nichts aus höheren Schichten importieren."""
    problems: list[str] = []
    for path in (ROOT / "models").glob("*.py"):
        for imp in internal_imports(path):
            if imp.split(".")[0] in HIGHER_LAYERS:
                problems.append(f"models/{path.name}: importiert aus höherer Schicht ('{imp}')")
    return problems


def check_solid(package: str, base_class: str, methods: set[str]) -> list[str]:
    """Prüft, dass jede Plugin-Datei genau eine Basisklasse mit den Methoden umsetzt."""
    problems: list[str] = []
    for path in (ROOT / package).glob("*.py"):
        if path.name in {"__init__.py", "base.py"}:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        impl = [c for c in classes if any(getattr(b, "id", "") == base_class for b in c.bases)]
        if len(impl) != 1:
            problems.append(f"{package}/{path.name}: erwartet genau eine {base_class}-Klasse")
            continue
        defined = {n.name for n in impl[0].body if isinstance(n, ast.FunctionDef)}
        if not methods <= defined:
            problems.append(f"{package}/{path.name}: {methods} unvollständig")
    return problems


def run_checks() -> dict[str, list[str]]:
    """Führt alle Prüfungen aus und liefert die Verstöße gruppiert zurück."""
    graph = build_graph()
    return {
        "cycles": [" -> ".join(c) for c in find_cycles(graph)],
        "models_layer": check_models_layer(),
        "independence_indicators": check_independence("indicators"),
        "independence_patterns": check_independence("patterns"),
        "independence_strategies": check_independence("strategies"),
        "independence_scores": check_independence("scores"),
        "independence_risk": check_independence("risk"),
        "independence_recommendation": check_independence("recommendation"),
        "solid_indicators": check_solid("indicators", "BaseIndicator", {"compute", "min_candles"}),
        "solid_patterns": check_solid("patterns", "BasePattern", {"detect", "min_candles"}),
        "solid_strategies": check_solid("strategies", "BaseStrategy", {"evaluate"}),
        "solid_scores": check_solid("scores", "BaseScoreModel", {"compute"}),
        "solid_risk": check_solid("risk", "BaseRiskModel", {"compute"}),
        "solid_recommendation": check_solid(
            "recommendation", "BaseRecommendationModel", {"compute"}
        ),
    }


def main() -> int:
    """CLI-Einstieg: druckt den Bericht und liefert den Exit-Code."""
    results = run_checks()
    total = sum(len(v) for v in results.values())
    for name, problems in results.items():
        print(f"{name}: {len(problems)} Verstöße")
        for problem in problems:
            print("   ", problem)
    print("\nERGEBNIS:", "BESTANDEN" if total == 0 else "FEHLGESCHLAGEN")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
