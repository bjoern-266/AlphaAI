"""Ableitung von Analyse-Dimensionen aus vorhandenen Trade-Daten.

Reine, deterministische Funktionen. Sie gewinnen die Dimensionen **Strategie**,
**Risiko-Level** und **Score** ausschließlich aus der ``recommendation_id`` bzw.
den ``reasons`` der bestehenden Empfehlung – ohne die Quelldaten zu verändern.
Damit sind alle abgeleiteten Labels vollständig **nachvollziehbar und
reproduzierbar**. Fehlt eine Information, ist das Label ``"unbekannt"`` bzw. der
Wert ``None`` (keine Erfindung von Daten).

Zusätzliche Dimensionen (z. B. ``pattern``, ``market_phase``) werden – sofern
vorhanden – aus der Metadata des Quell-Trades gelesen; das Framework ist damit
erweiterbar, ohne eine Engine zu ändern.
"""

from __future__ import annotations

import re

UNKNOWN = "unbekannt"

_RISK_RE = re.compile(r"\bRisk\s+(LOW|MEDIUM|HIGH)\b", re.IGNORECASE)
_RISK_PAREN_RE = re.compile(r"\((low|medium|high)\)", re.IGNORECASE)
_SCORE_RE = re.compile(r"(?<!Market )\bScore\s+(\d+(?:\.\d+)?)\s*/\s*100")


def parse_strategy(recommendation_id: str) -> str:
    """Leitet den Strategienamen aus der ``recommendation_id`` ab.

    Erwartetes Format ``rec:score:{strategie}:{richtung}:{symbol}:{zeit}``. Ist
    das Format unbekannt, wird ``"unbekannt"`` geliefert.
    """
    if not recommendation_id:
        return UNKNOWN
    tokens = recommendation_id.split(":")
    if len(tokens) >= 3 and tokens[0] == "rec" and tokens[1] == "score":
        return tokens[2] or UNKNOWN
    if len(tokens) >= 2 and tokens[0] == "score":
        return tokens[1] or UNKNOWN
    return UNKNOWN


def parse_risk_level(reasons: list[str]) -> str:
    """Leitet das Risiko-Level (``low``/``medium``/``high``) aus den Reasons ab."""
    for reason in reasons:
        match = _RISK_RE.search(reason) or _RISK_PAREN_RE.search(reason)
        if match:
            return match.group(1).lower()
    return UNKNOWN


def parse_score(reasons: list[str]) -> float | None:
    """Leitet den Score (0..100) aus den Reasons ab oder ``None``."""
    for reason in reasons:
        match = _SCORE_RE.search(reason)
        if match:
            return float(match.group(1))
    return None


def classify_outcome(pnl: float, breakeven_epsilon: float = 0.0) -> str:
    """Ordnet einem Ergebnis ``win``/``loss``/``breakeven`` zu."""
    if abs(pnl) <= breakeven_epsilon:
        return "breakeven"
    return "win" if pnl > 0 else "loss"


def score_band(score: float | None, weak_max: float, strong_min: float) -> str:
    """Ordnet einen Score einem Band (``low``/``medium``/``high``) zu."""
    if score is None:
        return UNKNOWN
    if score < weak_max:
        return "low"
    if score >= strong_min:
        return "high"
    return "medium"


def holding_band(days: float, bands: list[float]) -> str:
    """Ordnet eine Haltedauer (Tage) einem Bereich zu (z. B. ``"1-3"``)."""
    if days <= 0:
        return UNKNOWN
    lower = 0.0
    for upper in bands:
        if days <= upper:
            return f"{_fmt(lower)}-{_fmt(upper)}"
        lower = upper
    return f">{_fmt(lower)}"


def label_of(labels: dict[str, str], key: str) -> str:
    """Liest ein Dimensions-Label aus den Trade-Labels (Default ``"unbekannt"``)."""
    value = labels.get(key)
    return value if value else UNKNOWN


def _fmt(value: float) -> str:
    """Formatiert eine Bandgrenze ohne überflüssige Nachkommastellen."""
    return str(int(value)) if float(value).is_integer() else f"{value:g}"
