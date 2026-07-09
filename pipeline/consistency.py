"""Automatische Konsistenzprüfungen der Pipeline-Ergebnisse.

:func:`verify_pipeline` prüft, dass die Referenzen zwischen den Stufen eines
:class:`~models.pipeline.PipelineResult` exakt und eindeutig sind:

* jede Empfehlung besitzt **genau einen** RiskResult,
* jeder RiskResult besitzt **genau einen** ScoreResult,
* jeder ScoreResult besitzt **genau einen** StrategyResult,
* alle IDs sind eindeutig, alle Referenzen gültig.

Die Funktion liefert eine Liste von Verstößen (leer = konsistent) und wird von
der Integrations-Testsuite genutzt.
"""

from __future__ import annotations

from collections.abc import Sequence

from models.pipeline import PipelineResult


def _duplicates(ids: Sequence[str]) -> list[str]:
    """Gibt die mehrfach vorkommenden IDs zurück."""
    seen: set[str] = set()
    dupes: set[str] = set()
    for identifier in ids:
        if identifier in seen:
            dupes.add(identifier)
        seen.add(identifier)
    return sorted(dupes)


def verify_pipeline(result: PipelineResult) -> list[str]:
    """Prüft die Referenz- und Eindeutigkeits-Konsistenz eines Durchlaufs.

    Returns:
        Liste der Verstöße (leer = vollständig konsistent).
    """
    problems: list[str] = []

    strategies = result.strategies.results
    scores = result.scores.results
    risks = result.risks.results
    recommendations = result.recommendations.results

    # --- Eindeutigkeit der IDs ------------------------------------------------
    for label, ids in (
        ("StrategyResult.hypothesis_id", [s.hypothesis_id for s in strategies]),
        ("ScoreResult.score_id", [s.score_id for s in scores]),
        ("RiskResult.risk_id", [r.risk_id for r in risks]),
        ("RecommendationResult.recommendation_id", [r.recommendation_id for r in recommendations]),
    ):
        dupes = _duplicates(ids)
        if dupes:
            problems.append(f"Doppelte {label}: {dupes}")

    strategy_by_hyp = {s.hypothesis_id: s for s in strategies}
    score_by_hyp = {s.hypothesis_id: s for s in scores}
    risk_by_hyp = {r.hypothesis_id: r for r in risks}

    # --- Jeder ScoreResult besitzt genau einen StrategyResult -----------------
    for score in scores:
        if score.hypothesis_id not in strategy_by_hyp:
            problems.append(
                f"ScoreResult '{score.score_id}' ohne StrategyResult "
                f"(hypothesis_id '{score.hypothesis_id}')."
            )

    # --- Jeder RiskResult besitzt genau einen ScoreResult ---------------------
    for risk in risks:
        score = score_by_hyp.get(risk.hypothesis_id)
        if score is None:
            problems.append(
                f"RiskResult '{risk.risk_id}' ohne ScoreResult "
                f"(hypothesis_id '{risk.hypothesis_id}')."
            )
        elif risk.score_id != score.score_id:
            problems.append(
                f"RiskResult '{risk.risk_id}': score_id '{risk.score_id}' "
                f"≠ ScoreResult '{score.score_id}'."
            )

    # --- Jede Empfehlung besitzt genau einen Risk- und ScoreResult ------------
    for rec in recommendations:
        risk = risk_by_hyp.get(rec.hypothesis_id)
        if risk is None:
            problems.append(
                f"Recommendation '{rec.recommendation_id}' ohne RiskResult "
                f"(hypothesis_id '{rec.hypothesis_id}')."
            )
        elif rec.risk_id != risk.risk_id:
            problems.append(
                f"Recommendation '{rec.recommendation_id}': risk_id '{rec.risk_id}' "
                f"≠ RiskResult '{risk.risk_id}'."
            )
        score = score_by_hyp.get(rec.hypothesis_id)
        if score is None:
            problems.append(
                f"Recommendation '{rec.recommendation_id}' ohne ScoreResult "
                f"(hypothesis_id '{rec.hypothesis_id}')."
            )
        elif rec.score_id != score.score_id:
            problems.append(
                f"Recommendation '{rec.recommendation_id}': score_id '{rec.score_id}' "
                f"≠ ScoreResult '{score.score_id}'."
            )

    # --- Wertebereiche der Empfehlung -----------------------------------------
    for rec in recommendations:
        if not 0.0 <= rec.overall_rating <= 100.0:
            problems.append(
                f"Recommendation '{rec.recommendation_id}': Rating "
                f"{rec.overall_rating} außerhalb 0..100."
            )
        if not 0.0 <= rec.confidence <= 1.0:
            problems.append(
                f"Recommendation '{rec.recommendation_id}': Confidence "
                f"{rec.confidence} außerhalb 0..1."
            )

    return problems
