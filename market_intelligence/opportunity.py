"""Bewertungsmodelle und Aufbau einer einzelnen Chance.

Die fünf Bewertungsmodelle leiten ihren Score-Beitrag **ausschließlich** aus
einer **bereits vorhandenen** Kennzahl ab – sie berechnen **keine** neue
Handelsregel:

* :class:`RecommendationOpportunityModel` – aus dem Overall Rating der Empfehlung,
* :class:`RiskOpportunityModel` – aus dem Risiko-Faktor der Empfehlung,
* :class:`AnalyticsOpportunityModel` – aus der Win Rate des Analytics-Reports,
* :class:`BacktestOpportunityModel` – aus der Win Rate des Backtest-Reports,
* :class:`PaperTradingOpportunityModel` – aus der Win Rate des Paper-Trading-Reports.

:func:`build_opportunity` fasst die Beiträge (mit ihren Gewichten aus der
Regeldatei) zu einem gewichteten ``opportunity_score`` zusammen und übernimmt
Richtung/Stärke/Confidence/Rating/Risiko **unverändert** aus der Empfehlung.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from market_intelligence.base import (
    BaseOpportunityModel,
    clamp_score,
    require_weight,
)
from models.opportunity import (
    MarketCandidate,
    MarketIntelligenceContext,
    Opportunity,
    OpportunityModelOutput,
)
from models.recommendation import Direction, RecommendationResult, RecommendationStrength

# Namen der fünf Score-Komponenten (zugleich die TOML-Abschnittsnamen).
RECOMMENDATION = "recommendation"
RISK = "risk"
ANALYTICS = "analytics"
BACKTEST = "backtest"
PAPER_TRADING = "paper_trading"


def _risk_factor(recommendation: RecommendationResult | None) -> float | None:
    """Liest den Risiko-Faktor (0..100, höher = geringeres Risiko) der Empfehlung."""
    if recommendation is None or not isinstance(recommendation.metadata, dict):
        return None
    factors = recommendation.metadata.get("factors", {})
    value = factors.get("risk") if isinstance(factors, dict) else None
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


class RecommendationOpportunityModel(BaseOpportunityModel):
    """Beitrag aus dem **bestehenden** Overall Rating der Empfehlung."""

    name = RECOMMENDATION
    source = "RecommendationResult.overall_rating"

    def compute(
        self, context: MarketIntelligenceContext, params: Mapping[str, Any]
    ) -> OpportunityModelOutput:
        """Übernimmt das Overall Rating (0..100) als Score-Beitrag."""
        weight = require_weight(params, self.name)
        rec = context.candidate.recommendation
        if rec is None:
            return OpportunityModelOutput(
                self.name, 0.0, weight, available=False, reasons=["Keine Empfehlung vorhanden."]
            )
        score = clamp_score(rec.overall_rating, context.config)
        reasons = [
            f"Overall Rating {rec.overall_rating:.0f}/100",
            f"Confidence {rec.confidence * 100:.0f}%",
        ]
        return OpportunityModelOutput(self.name, score, weight, reasons=reasons)


class RiskOpportunityModel(BaseOpportunityModel):
    """Beitrag aus dem **bestehenden** Risiko-Faktor der Empfehlung."""

    name = RISK
    source = "RecommendationResult.metadata['factors']['risk']"

    def compute(
        self, context: MarketIntelligenceContext, params: Mapping[str, Any]
    ) -> OpportunityModelOutput:
        """Übernimmt den Risiko-Faktor (0..100, höher = geringeres Risiko)."""
        weight = require_weight(params, self.name)
        factor = _risk_factor(context.candidate.recommendation)
        if factor is None:
            return OpportunityModelOutput(
                self.name, 0.0, weight, available=False, reasons=["Kein Risiko-Faktor vorhanden."]
            )
        score = clamp_score(factor, context.config)
        return OpportunityModelOutput(
            self.name,
            score,
            weight,
            reasons=[f"Risiko-Faktor {factor:.0f}/100 (höher = geringeres Risiko)"],
        )


class _WinRateModel(BaseOpportunityModel):
    """Basis für Modelle, die eine **bestehende** Win Rate (0..1) übernehmen."""

    label = "Quelle"

    def _win_rate(self, candidate: MarketCandidate) -> float | None:
        """Liest die Win Rate der jeweiligen Quelle (0..1) oder ``None``."""
        raise NotImplementedError

    def compute(
        self, context: MarketIntelligenceContext, params: Mapping[str, Any]
    ) -> OpportunityModelOutput:
        """Rechnet die Win Rate (0..1) rein darstellerisch auf 0..100 hoch."""
        weight = require_weight(params, self.name)
        win_rate = self._win_rate(context.candidate)
        if win_rate is None:
            return OpportunityModelOutput(
                self.name, 0.0, weight, available=False, reasons=[f"Kein {self.label} vorhanden."]
            )
        score = clamp_score(win_rate * 100.0, context.config)
        return OpportunityModelOutput(
            self.name, score, weight, reasons=[f"{self.label}: Win Rate {win_rate * 100:.0f}%"]
        )


class AnalyticsOpportunityModel(_WinRateModel):
    """Beitrag aus der **bestehenden** Win Rate des Analytics-Reports."""

    name = ANALYTICS
    source = "AnalyticsReport.result.win_rate"
    label = "Analytics"

    def _win_rate(self, candidate: MarketCandidate) -> float | None:
        """Win Rate aus dem Analytics-Ergebnis (0..1) oder ``None``."""
        result = getattr(candidate.analytics, "result", None)
        return getattr(result, "win_rate", None)


class BacktestOpportunityModel(_WinRateModel):
    """Beitrag aus der **bestehenden** Win Rate des Backtest-Reports."""

    name = BACKTEST
    source = "BacktestReport.results[0].win_rate"
    label = "Backtest"

    def _win_rate(self, candidate: MarketCandidate) -> float | None:
        """Win Rate aus dem ersten Backtest-Ergebnis (0..1) oder ``None``."""
        results = getattr(candidate.backtest, "results", None) or []
        return results[0].win_rate if results else None


class PaperTradingOpportunityModel(_WinRateModel):
    """Beitrag aus der **bestehenden** Win Rate des Paper-Trading-Reports."""

    name = PAPER_TRADING
    source = "PaperTradingReport.statistics.win_rate"
    label = "Paper Trading"

    def _win_rate(self, candidate: MarketCandidate) -> float | None:
        """Win Rate aus der Paper-Trading-Statistik (0..1) oder ``None``."""
        stats = getattr(candidate.paper_trading, "statistics", None)
        return getattr(stats, "win_rate", None)


def _analytics_summary(candidate: MarketCandidate) -> str:
    """Übernimmt die bereits vorhandene Analytics-Kurzfassung."""
    result = getattr(candidate.analytics, "result", None)
    return str(getattr(result, "summary", "")) if result is not None else ""


def _backtest_summary(candidate: MarketCandidate) -> str:
    """Übernimmt die bereits vorhandene Backtest-Kurzfassung."""
    results = getattr(candidate.backtest, "results", None) or []
    return str(getattr(results[0], "summary", "")) if results else ""


def _paper_summary(candidate: MarketCandidate) -> str:
    """Erzeugt eine kurze Paper-Trading-Kurzfassung aus vorhandenen Kennzahlen."""
    stats = getattr(candidate.paper_trading, "statistics", None)
    if stats is None:
        return ""
    return (
        f"Win Rate {stats.win_rate * 100:.0f}% · "
        f"Profit Factor {stats.profit_factor:.2f} · "
        f"{stats.closed_positions} Trades"
    )


def _combine_score(
    outputs: Mapping[str, OpportunityModelOutput], config: Mapping[str, Any]
) -> float:
    """Gewichtete Zusammenfassung der **verfügbaren** Komponenten (0..100).

    Fehlt eine Quelle, wird ihr Beitrag ausgelassen und über die verbleibenden
    Gewichte normalisiert – es wird **nichts** ersatzweise berechnet.
    """
    available = [out for out in outputs.values() if out.available]
    total_weight = sum(out.weight for out in available)
    if total_weight <= 0.0:
        return clamp_score(0.0, config)
    weighted = sum(out.score * out.weight for out in available)
    return clamp_score(weighted / total_weight, config)


def build_opportunity(
    context: MarketIntelligenceContext, outputs: Mapping[str, OpportunityModelOutput]
) -> Opportunity:
    """Baut aus den Modell-Beiträgen eine einzelne :class:`Opportunity`.

    Richtung, Stärke, Confidence, Rating und Risiko werden **unverändert** aus der
    Empfehlung übernommen. Der ``opportunity_score`` ist die gewichtete
    Zusammenfassung der Beiträge; der ``opportunity_rank`` wird später im Ranking
    vergeben (hier ``0``).
    """
    candidate = context.candidate
    rec = candidate.recommendation
    score = _combine_score(outputs, context.config)

    direction = rec.direction if rec is not None else Direction.NEUTRAL
    strength = rec.recommendation_strength if rec is not None else RecommendationStrength.REJECT
    confidence = rec.confidence if rec is not None else 0.0
    overall_rating = rec.overall_rating if rec is not None else 0.0
    risk = _risk_factor(rec)

    reasons: list[str] = []
    warnings: list[str] = []
    for out in outputs.values():
        if out.available:
            reasons.extend(f"[{out.name}] {reason}" for reason in out.reasons)
        warnings.extend(out.warnings)
    if rec is not None:
        reasons.extend(rec.reasons)
        warnings.extend(rec.warnings)

    summary = f"{direction.value.upper()} · {strength.value} · " f"Opportunity {score:.0f}/100"
    return Opportunity(
        ticker=candidate.ticker,
        company=candidate.company,
        market=candidate.market,
        direction=direction,
        recommendation_strength=strength,
        confidence=confidence,
        overall_rating=overall_rating,
        risk=risk,
        opportunity_score=score,
        opportunity_rank=0,
        summary=summary,
        sector=candidate.sector,
        exchange=candidate.exchange,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
        pattern_summary=candidate.pattern_summary,
        strategy_summary=candidate.strategy_summary,
        analytics_summary=_analytics_summary(candidate),
        backtest_summary=_backtest_summary(candidate),
        paper_trading_summary=_paper_summary(candidate),
        components={name: out.score for name, out in outputs.items()},
        timestamp=datetime.now(UTC),
        metadata={"available": {name: out.available for name, out in outputs.items()}},
    )
