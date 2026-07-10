"""Paper Runner: tägliche Simulation über die bestehende Pipeline.

Der :class:`PaperRunner` lässt (Live-/historische) Marktdaten **tagweise** durch
den bestehenden :class:`~pipeline.runner.IntegrationRunner` laufen. An jedem Tag:

1. werden die offenen Positionen zum Tageskurs bewertet (Mark-to-Market) und bei
   Stop/Take-Profit geschlossen,
2. verfallen zu alte Positionen (Expire),
3. wird die bestehende Pipeline auf den Daten **bis einschließlich** dieses Tages
   ausgewertet und – falls die Empfehlung actionable ist – eine neue Position im
   simulierten Portfolio eröffnet.

Es wird **keine** echte Order ausgeführt und **keine** Empfehlung verändert. Die
Positionsgröße, Stop- und Take-Profit-Abstände stammen aus der bestehenden Risk
Engine (und damit aus ``settings.toml``); Konto-/Risikowerte kommen nicht aus den
Paper-Trading-Regeln.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from core.exceptions import PaperTradingValidationError
from models.market import COL_CLOSE, COL_HIGH, COL_LOW
from models.paper_trading import CloseReason
from models.pipeline import PipelineResult
from models.recommendation import Direction, RecommendationResult, SuggestedAction
from models.risk import RiskResult
from paper_trading.portfolio import PaperPortfolio
from pipeline.runner import IntegrationRunner


@dataclass(frozen=True, slots=True)
class PaperRunnerParams:
    """Parameter des Paper Runners (aus ``paper_trading_rules.toml``).

    Attributes:
        warmup_bars: Vorlauf in Kerzen, bevor Empfehlungen ausgewertet werden.
        step: Schrittweite in Kerzen zwischen zwei Empfehlungs-Auswertungen
            (1 = täglich).
        max_holding_days: Maximale Haltedauer in Tagen bis zum Verfall (Expire).
        trailing_distance: Trailing-Stop-Abstand (**vorbereitet**, 0 = inaktiv).
    """

    warmup_bars: int = 200
    step: int = 1
    max_holding_days: int = 10
    trailing_distance: float = 0.0


class PaperRunner:
    """Treibt die tägliche Paper-Trading-Simulation eines Symbols.

    Args:
        runner: Der vollständige :class:`IntegrationRunner` (unveränderte Kette).
        params: Parameter des Paper Runners.
    """

    def __init__(self, runner: IntegrationRunner, params: PaperRunnerParams) -> None:
        self._runner = runner
        self._params = params

    def run(
        self,
        frame: pd.DataFrame,
        symbol: str,
        portfolio: PaperPortfolio,
        max_open_positions: int,
        timeframe: str = "base",
    ) -> list[str]:
        """Simuliert das Symbol tagweise und füllt das Portfolio.

        Returns:
            Gesammelte Warnungen (z. B. übersprungene Signale).
        """
        warnings: list[str] = []
        highs = frame[COL_HIGH].to_numpy(dtype=float)
        lows = frame[COL_LOW].to_numpy(dtype=float)
        closes = frame[COL_CLOSE].to_numpy(dtype=float)
        timestamps = list(frame.index)
        n = len(closes)

        first = max(self._params.warmup_bars - 1, 0)
        for index in range(first, n):
            timestamp = _as_datetime(timestamps[index])
            close = float(closes[index])
            # 1. Offene Positionen bewerten/schließen.
            portfolio.update_market(
                float(highs[index]),
                float(lows[index]),
                close,
                timestamp,
                self._params.trailing_distance,
            )
            # 2. Verfall zu alter Positionen.
            self._expire(portfolio, index, close, timestamp)
            # 3. Neue Empfehlung auswerten (im Schrittraster).
            if (index - first) % max(self._params.step, 1) == 0:
                self._maybe_open(
                    portfolio,
                    frame,
                    symbol,
                    index,
                    close,
                    timestamp,
                    max_open_positions,
                    warnings,
                    timeframe,
                )
        return warnings

    def _expire(
        self, portfolio: PaperPortfolio, index: int, close: float, timestamp: datetime | None
    ) -> None:
        """Schließt Positionen, deren Haltedauer die Obergrenze erreicht hat."""
        for position in portfolio.open_positions():
            entry_index = position.metadata.get("entry_index")
            if entry_index is None:
                continue
            if index - int(entry_index) >= self._params.max_holding_days:
                portfolio.close_position(position.position_id, close, timestamp, CloseReason.EXPIRE)

    def _maybe_open(
        self,
        portfolio: PaperPortfolio,
        frame: pd.DataFrame,
        symbol: str,
        index: int,
        close: float,
        timestamp: datetime | None,
        max_open_positions: int,
        warnings: list[str],
        timeframe: str,
    ) -> None:
        """Eröffnet – falls actionable – eine neue Position aus der Empfehlung."""
        result = self._runner.run_frame(frame.iloc[: index + 1], symbol, timeframe)
        recommendation = self._actionable(result)
        if recommendation is None:
            return
        if portfolio.has_open_for_recommendation(recommendation.recommendation_id):
            return
        if len(portfolio.open_positions()) >= max_open_positions:
            return
        risk = _risk_for(result, recommendation)
        if risk is None or risk.estimated_shares <= 0 or risk.suggested_stop_distance <= 0:
            return

        stop_distance = float(risk.suggested_stop_distance)
        tp_distance = float(risk.suggested_take_profit)
        if recommendation.direction is Direction.SHORT:
            stop_price = close + stop_distance
            take_profit_price = max(0.0, close - tp_distance)
        else:
            stop_price = max(0.0, close - stop_distance)
            take_profit_price = close + tp_distance

        try:
            portfolio.open_position(
                recommendation_id=recommendation.recommendation_id,
                symbol=symbol,
                direction=recommendation.direction,
                recommendation_strength=recommendation.recommendation_strength,
                entry_price=close,
                stop_price=stop_price,
                take_profit_price=take_profit_price,
                shares=float(risk.estimated_shares),
                risk_amount=float(risk.estimated_shares) * stop_distance,
                entry_time=timestamp,
                reasons=list(recommendation.reasons),
                warnings=list(recommendation.warnings),
                metadata={"entry_index": index},
            )
        except PaperTradingValidationError as error:
            warnings.append(f"Position nicht eröffnet ({index}): {error}")

    @staticmethod
    def _actionable(result: PipelineResult) -> RecommendationResult | None:
        """Gibt die beste actionable Empfehlung zurück (oder ``None``)."""
        if not result.recommendations.valid:
            return None
        recommendation = result.best()
        if recommendation is None:
            return None
        if (
            recommendation.direction is Direction.NEUTRAL
            or recommendation.suggested_action is not SuggestedAction.OPEN
        ):
            return None
        return recommendation


def _risk_for(result: PipelineResult, recommendation: RecommendationResult) -> RiskResult | None:
    """Sucht die Risikobewertung zur Empfehlung (über die ``risk_id``)."""
    for risk in result.risks.results:
        if risk.risk_id == recommendation.risk_id:
            return risk
    return None


def _as_datetime(value: object) -> datetime | None:
    """Wandelt einen Index-Eintrag – falls möglich – in ein ``datetime`` um."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    return None
