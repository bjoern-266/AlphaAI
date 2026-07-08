"""FVG-Strategie – Hypothese aus Fair Value Gap und Trendfilter.

Kombiniert ein (optional frisches) Fair Value Gap mit dem übergeordneten Trend
(EMA200) zu einer Fortsetzungs-Hypothese. Unabhängig von allen anderen
Strategien. Erzeugt ausschließlich eine Hypothese, keine Kaufentscheidung.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from strategies.base import (
    BaseStrategy,
    StrategyContext,
    StrategyDirection,
    StrategyEvaluation,
    StrategyResult,
    build_hypothesis_id,
    direction_from_value,
    require_bool,
    require_float,
)


class FvgStrategy(BaseStrategy):
    """Hypothese: Fortsetzung an einem Fair Value Gap im Trend."""

    name = "fvg_strategy"
    description = "Fortsetzung an einem Fair Value Gap in Richtung des EMA200-Trends."
    version = "1.0"
    pattern_requirements = ("fvg",)
    indicator_requirements = ("ema",)

    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        """Erzeugt eine Fortsetzungs-Hypothese, wenn FVG und Trend übereinstimmen."""
        confidence = require_float(params, "base_confidence", self.name)
        require_fresh = require_bool(params, "require_fresh", self.name)

        candidates = context.patterns.by_name("fvg")
        if require_fresh:
            candidates = [f for f in candidates if f.metadata.get("fresh")]
        if not candidates:
            return StrategyEvaluation(warnings=["Kein passendes FVG vorhanden."])

        fvg = max(candidates, key=lambda p: (p.timestamp is not None, p.timestamp))
        direction = direction_from_value(fvg.direction.value)
        close = context.last_close
        ema200 = context.indicators.ema200

        aligned, trend_reason = self._trend_alignment(direction, close, ema200)
        if not aligned:
            return StrategyEvaluation(warnings=[f"FVG ({direction.value}) widerspricht dem Trend."])

        hypothesis = (
            "Bullische Fortsetzung an Fair Value Gap"
            if direction is StrategyDirection.BULLISH
            else "Bärische Fortsetzung an Fair Value Gap"
        )
        reasons = [
            f"{'Frisches ' if require_fresh else ''}FVG ({direction.value}) erkannt.",
            trend_reason,
        ]

        result = StrategyResult(
            strategy_name=self.name,
            hypothesis_id=build_hypothesis_id(self.name, direction, context.symbol, fvg.timestamp),
            direction=direction,
            confidence=confidence,
            strength=fvg.strength,
            matched_indicators=["ema"],
            matched_patterns=["fvg"],
            reasons=reasons,
            metadata={"hypothesis": hypothesis, "gap_level": fvg.price_level},
            timestamp=fvg.timestamp,
        )
        return StrategyEvaluation(result=result)

    @staticmethod
    def _trend_alignment(
        direction: StrategyDirection, close: float | None, ema200: float | None
    ) -> tuple[bool, str]:
        """Prüft, ob die FVG-Richtung zum EMA200-Trend passt."""
        if close is None or ema200 is None:
            return True, "Kein Trendfilter (EMA200/Kurs fehlt) – Richtung des FVG übernommen."
        if direction is StrategyDirection.BULLISH:
            return close >= ema200, "Kurs über EMA200 (Aufwärtsbias)."
        return close <= ema200, "Kurs unter EMA200 (Abwärtsbias)."
