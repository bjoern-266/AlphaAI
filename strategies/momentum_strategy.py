"""Momentum-Strategie – Hypothese aus RSI und MACD-Histogramm.

Bildet eine Momentum-Hypothese, wenn RSI und MACD-Histogramm in dieselbe
Richtung zeigen. Unabhängig von allen anderen Strategien. Erzeugt ausschließlich
eine Hypothese.
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


class MomentumStrategy(BaseStrategy):
    """Hypothese: anhaltendes Momentum anhand RSI und MACD-Histogramm."""

    name = "momentum_strategy"
    description = "Momentum, wenn RSI und MACD-Histogramm dieselbe Richtung bestätigen."
    version = "1.0"
    indicator_requirements = ("rsi", "macd")

    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        """Erzeugt eine Momentum-Hypothese bei Übereinstimmung von RSI und MACD."""
        confidence = require_float(params, "base_confidence", self.name)
        rsi_bull = require_float(params, "rsi_bull", self.name)
        rsi_bear = require_float(params, "rsi_bear", self.name)

        rsi = context.indicators.rsi14
        histogram = context.indicators.macd_histogram
        if rsi is None or histogram is None:
            return StrategyEvaluation(warnings=["RSI oder MACD-Histogramm nicht verfügbar."])

        if rsi >= rsi_bull and histogram > 0:
            direction = StrategyDirection.BULLISH
            hypothesis = "Bullisches Momentum"
        elif rsi <= rsi_bear and histogram < 0:
            direction = StrategyDirection.BEARISH
            hypothesis = "Bärisches Momentum"
        else:
            return StrategyEvaluation(
                warnings=["RSI und MACD-Histogramm bestätigen kein Momentum."]
            )

        result = StrategyResult(
            strategy_name=self.name,
            hypothesis_id=build_hypothesis_id(
                self.name, direction, context.symbol, context.last_timestamp
            ),
            direction=direction,
            confidence=confidence,
            strength=float(min(100.0, abs(rsi - 50.0) * 2.0)),
            matched_indicators=["rsi", "macd"],
            matched_patterns=[],
            reasons=[
                f"RSI {rsi:.1f} ({'≥' if direction is StrategyDirection.BULLISH else '≤'} "
                f"{rsi_bull if direction is StrategyDirection.BULLISH else rsi_bear}).",
                f"MACD-Histogramm {histogram:.4f} bestätigt die Richtung.",
            ],
            metadata={"hypothesis": hypothesis, "rsi": rsi, "macd_histogram": histogram},
            timestamp=context.last_timestamp,
        )
        return StrategyEvaluation(result=result)
