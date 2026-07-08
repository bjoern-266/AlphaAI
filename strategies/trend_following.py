"""Trend-Following-Strategie – Hypothese aus EMA-Fächer und ADX.

Bildet eine Trendfortsetzungs-Hypothese, wenn die EMAs gestaffelt sind und der
ADX eine tragfähige Trendstärke anzeigt. Unabhängig von allen anderen
Strategien. Erzeugt ausschließlich eine Hypothese.
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
    require_float,
)


class TrendFollowingStrategy(BaseStrategy):
    """Hypothese: Trendfortsetzung anhand gestaffelter EMAs und ADX."""

    name = "trend_following"
    description = "Trendfortsetzung bei gestaffelten EMAs (20/50/200) und tragfähigem ADX."
    version = "1.0"
    indicator_requirements = ("ema", "adx")

    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        """Erzeugt eine Trendhypothese, wenn EMA-Fächer und ADX übereinstimmen."""
        confidence = require_float(params, "base_confidence", self.name)
        adx_min = require_float(params, "adx_min", self.name)

        ema20 = context.indicators.ema20
        ema50 = context.indicators.ema50
        ema200 = context.indicators.ema200
        adx = context.indicators.adx
        if None in (ema20, ema50, ema200, adx):
            return StrategyEvaluation(warnings=["EMA-Fächer oder ADX nicht verfügbar."])

        if adx < adx_min:
            return StrategyEvaluation(warnings=[f"ADX {adx:.1f} < {adx_min} – kein Trend."])

        if ema20 > ema50 > ema200:
            direction = StrategyDirection.BULLISH
            fan = "EMA20 > EMA50 > EMA200 (Aufwärtsfächer)."
            hypothesis = "Bullische Trendfortsetzung"
        elif ema20 < ema50 < ema200:
            direction = StrategyDirection.BEARISH
            fan = "EMA20 < EMA50 < EMA200 (Abwärtsfächer)."
            hypothesis = "Bärische Trendfortsetzung"
        else:
            return StrategyEvaluation(warnings=["Kein eindeutiger EMA-Fächer."])

        result = StrategyResult(
            strategy_name=self.name,
            hypothesis_id=build_hypothesis_id(
                self.name, direction, context.symbol, context.last_timestamp
            ),
            direction=direction,
            confidence=confidence,
            strength=float(min(100.0, adx)),
            matched_indicators=["ema", "adx"],
            matched_patterns=[],
            reasons=[fan, f"ADX {adx:.1f} ≥ {adx_min} (tragfähiger Trend)."],
            metadata={"hypothesis": hypothesis, "adx": adx},
            timestamp=context.last_timestamp,
        )
        return StrategyEvaluation(result=result)
