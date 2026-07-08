"""Breakout-Strategie – Hypothese aus Break of Structure und Volumen.

Bildet eine Ausbruchs-Hypothese, wenn ein Break of Structure (BOS) von
überdurchschnittlichem relativem Volumen begleitet wird. Unabhängig von allen
anderen Strategien. Erzeugt ausschließlich eine Hypothese.
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
    require_float,
)


class BreakoutStrategy(BaseStrategy):
    """Hypothese: bestätigter Ausbruch aus BOS und relativem Volumen."""

    name = "breakout_strategy"
    description = (
        "Ausbruch, wenn ein Break of Structure von hohem relativem Volumen begleitet wird."
    )
    version = "1.0"
    pattern_requirements = ("bos",)
    indicator_requirements = ("relative_volume",)

    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        """Erzeugt eine Ausbruchs-Hypothese bei BOS mit Volumenbestätigung."""
        confidence = require_float(params, "base_confidence", self.name)
        rvol_min = require_float(params, "rvol_min", self.name)

        breaks = context.patterns.by_name("bos")
        if not breaks:
            return StrategyEvaluation(warnings=["Kein Break of Structure vorhanden."])

        rvol = context.indicators.relative_volume
        if rvol is None:
            return StrategyEvaluation(warnings=["Relatives Volumen nicht verfügbar."])
        if rvol < rvol_min:
            return StrategyEvaluation(
                warnings=[f"Relatives Volumen {rvol:.2f} < {rvol_min} – Ausbruch unbestätigt."]
            )

        bos = max(breaks, key=lambda p: (p.timestamp is not None, p.timestamp))
        direction = direction_from_value(bos.direction.value)
        hypothesis = (
            "Bullischer Ausbruch (BOS + Volumen)"
            if direction is StrategyDirection.BULLISH
            else "Bärischer Ausbruch (BOS + Volumen)"
        )

        result = StrategyResult(
            strategy_name=self.name,
            hypothesis_id=build_hypothesis_id(self.name, direction, context.symbol, bos.timestamp),
            direction=direction,
            confidence=confidence,
            strength=bos.strength,
            matched_indicators=["relative_volume"],
            matched_patterns=["bos"],
            reasons=[
                f"Break of Structure ({direction.value}) bei {bos.price_level}.",
                f"Relatives Volumen {rvol:.2f} ≥ {rvol_min} bestätigt den Ausbruch.",
            ],
            metadata={"hypothesis": hypothesis, "relative_volume": rvol},
            timestamp=bos.timestamp,
        )
        return StrategyEvaluation(result=result)
