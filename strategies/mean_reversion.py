"""Mean-Reversion-Strategie – Hypothese aus RSI-Extrem und Bollinger-Band.

Bildet eine Gegenbewegungs-Hypothese, wenn der RSI ein Extrem erreicht und der
Kurs das äußere Bollinger-Band berührt/überschreitet. Unabhängig von allen
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
    require_float,
)


class MeanReversionStrategy(BaseStrategy):
    """Hypothese: Gegenbewegung aus RSI-Extrem und Bollinger-Band-Berührung."""

    name = "mean_reversion"
    description = "Gegenbewegung bei RSI-Extrem und Berührung des äußeren Bollinger-Bands."
    version = "1.0"
    indicator_requirements = ("rsi", "bollinger")

    def evaluate(self, context: StrategyContext, params: Mapping[str, Any]) -> StrategyEvaluation:
        """Erzeugt eine Gegenbewegungs-Hypothese bei RSI-Extrem und Bandberührung."""
        confidence = require_float(params, "base_confidence", self.name)
        oversold = require_float(params, "rsi_oversold", self.name)
        overbought = require_float(params, "rsi_overbought", self.name)

        rsi = context.indicators.rsi14
        if rsi is None:
            return StrategyEvaluation(warnings=["RSI nicht verfügbar."])
        bands = context.indicators.bollinger_bands
        close = context.last_close

        if rsi <= oversold and self._touches_lower(close, bands["lower"]):
            direction = StrategyDirection.BULLISH
            hypothesis = "Bullische Gegenbewegung (überverkauft)"
            reason = f"RSI {rsi:.1f} ≤ {oversold} und Kurs am unteren Bollinger-Band."
        elif rsi >= overbought and self._touches_upper(close, bands["upper"]):
            direction = StrategyDirection.BEARISH
            hypothesis = "Bärische Gegenbewegung (überkauft)"
            reason = f"RSI {rsi:.1f} ≥ {overbought} und Kurs am oberen Bollinger-Band."
        else:
            return StrategyEvaluation(warnings=["Kein RSI-Extrem mit Bandberührung."])

        result = StrategyResult(
            strategy_name=self.name,
            hypothesis_id=build_hypothesis_id(
                self.name, direction, context.symbol, context.last_timestamp
            ),
            direction=direction,
            confidence=confidence,
            strength=float(min(100.0, abs(rsi - 50.0) * 2.0)),
            matched_indicators=["rsi", "bollinger"],
            matched_patterns=[],
            reasons=[reason],
            metadata={"hypothesis": hypothesis, "rsi": rsi},
            timestamp=context.last_timestamp,
        )
        return StrategyEvaluation(result=result)

    @staticmethod
    def _touches_lower(close: float | None, lower: float | None) -> bool:
        """Gibt zurück, ob der Kurs das untere Band berührt (oder Band fehlt)."""
        return lower is None or close is None or close <= lower

    @staticmethod
    def _touches_upper(close: float | None, upper: float | None) -> bool:
        """Gibt zurück, ob der Kurs das obere Band berührt (oder Band fehlt)."""
        return upper is None or close is None or close >= upper
