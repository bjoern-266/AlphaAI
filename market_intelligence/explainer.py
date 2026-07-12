"""Transparente Herleitung einer Chance (keine Blackbox).

Der Explainer erklärt für jede **bereits bewertete** Chance ihren Platz: welche
Faktoren entscheidend waren, welche Risiken bestehen und warum sie nicht höher
steht. Es findet **keine** Berechnung statt – es werden ausschließlich die
vorhandenen Werte der :class:`~models.opportunity.Opportunity` erklärt.
"""

from __future__ import annotations

from collections.abc import Sequence

from models.opportunity import Opportunity, OpportunityExplanation

# Anzeigenamen der Score-Komponenten (nur für die Erklärung).
_COMPONENT_TITLES = {
    "recommendation": "Empfehlung",
    "risk": "Risiko",
    "analytics": "Analytics",
    "backtest": "Backtesting",
    "paper_trading": "Paper Trading",
}


def _headline(opportunity: Opportunity) -> str:
    """Kernaussage zum Platz einer Chance."""
    return (
        f"Platz {opportunity.opportunity_rank}: "
        f"{opportunity.ticker} · {opportunity.direction.value.upper()} · "
        f"Opportunity Score {opportunity.opportunity_score:.0f}/100"
    )


def _factors(opportunity: Opportunity, limit: int = 3) -> tuple[str, ...]:
    """Die stärksten Komponenten (entscheidende Faktoren) einer Chance."""
    ordered = sorted(opportunity.components.items(), key=lambda item: item[1], reverse=True)
    return tuple(
        f"{_COMPONENT_TITLES.get(name, name)}: {value:.0f}/100" for name, value in ordered[:limit]
    )


def _risks(opportunity: Opportunity) -> tuple[str, ...]:
    """Die bestehenden Risiken/Warnungen einer Chance."""
    risks = list(opportunity.warnings)
    if opportunity.risk is not None:
        risks.append(f"Risiko-Faktor {opportunity.risk:.0f}/100 (höher = geringeres Risiko)")
    return tuple(risks)


def _why_not_higher(opportunity: Opportunity, above: Opportunity | None) -> str:
    """Erklärt, warum die Chance nicht höher steht (Vergleich nach oben)."""
    if above is None:
        return "Höchste Gesamtchance im aktuellen Feld."
    gap = above.opportunity_score - opportunity.opportunity_score
    return (
        f"Platz {above.opportunity_rank} ({above.ticker}) liegt mit "
        f"{above.opportunity_score:.0f}/100 um {gap:.0f} Punkte vorn."
    )


def explain(opportunity: Opportunity, above: Opportunity | None = None) -> OpportunityExplanation:
    """Baut die Herleitung einer einzelnen Chance."""
    return OpportunityExplanation(
        ticker=opportunity.ticker,
        rank=opportunity.opportunity_rank,
        opportunity_score=opportunity.opportunity_score,
        headline=_headline(opportunity),
        factors=_factors(opportunity),
        risks=_risks(opportunity),
        why_not_higher=_why_not_higher(opportunity, above),
    )


def build_explanations(
    ranked: Sequence[Opportunity],
) -> dict[str, OpportunityExplanation]:
    """Baut die Herleitung für alle Chancen (in Ranking-Reihenfolge)."""
    explanations: dict[str, OpportunityExplanation] = {}
    previous: Opportunity | None = None
    for opportunity in ranked:
        explanations[opportunity.ticker] = explain(opportunity, previous)
        previous = opportunity
    return explanations
