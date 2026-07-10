"""Historical Runner: die bestehende Pipeline über die Historie ausführen.

Der :class:`HistoricalRunner` lässt historische Marktdaten **zeitpunktweise**
durch den bestehenden :class:`~pipeline.runner.IntegrationRunner` laufen. An
jedem Auswertungspunkt sieht die Pipeline ausschließlich die Kerzen **bis
einschließlich** dieses Zeitpunkts (kein Blick in die Zukunft) und erzeugt – mit
der **unveränderten** Fachlogik – eine Empfehlung. Diese Empfehlung wird als
:class:`~models.backtest.HistoricalSignal` gesammelt.

Der Runner trifft **keine** eigene Entscheidung und ändert **keine** Empfehlung.
Er sammelt lediglich die bestehenden Empfehlungen ein, damit der Trade-Simulator
bewerten kann, wie sie sich entwickelt hätten. Positionsgröße, Stop- und
Take-Profit-Abstände stammen aus der Risk Engine (und damit aus
``settings.toml``); es entsteht keine neue Handelsregel.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

from models.backtest import HistoricalSignal
from models.market import COL_CLOSE
from models.pipeline import PipelineResult
from models.recommendation import RecommendationResult
from models.risk import RiskResult
from pipeline.runner import IntegrationRunner


@dataclass(frozen=True, slots=True)
class HistoricalRunnerParams:
    """Parameter des Historical Runners (aus ``backtest_rules.toml``).

    Attributes:
        warmup_bars: Anzahl der Kerzen, die als Vorlauf gebraucht werden, bevor
            der erste Auswertungspunkt ausgewertet wird (genug Historie für die
            Indikatoren, z. B. EMA200).
        step: Schrittweite in Kerzen zwischen zwei Auswertungspunkten.
        min_history_bars: Mindestlänge der Historie, damit überhaupt ausgewertet
            wird.
    """

    warmup_bars: int = 200
    step: int = 5
    min_history_bars: int = 210


class HistoricalRunner:
    """Führt die bestehende Pipeline über die Historie aus und sammelt Signale.

    Args:
        runner: Der vollständige :class:`IntegrationRunner` (unveränderte Kette).
        params: Parameter des Historical Runners.
    """

    def __init__(self, runner: IntegrationRunner, params: HistoricalRunnerParams) -> None:
        self._runner = runner
        self._params = params

    def generate(
        self, frame: pd.DataFrame, symbol: str, timeframe: str = "base"
    ) -> tuple[list[HistoricalSignal], list[str]]:
        """Erzeugt die historischen Signale für ein Symbol.

        Args:
            frame: Vollständiger historischer OHLCV-DataFrame.
            symbol: Symbolname.
            timeframe: Zeitebenen-Label.

        Returns:
            Ein Tupel ``(signals, warnings)``.
        """
        warnings: list[str] = []
        signals: list[HistoricalSignal] = []
        if frame is None or frame.empty or COL_CLOSE not in frame.columns:
            return signals, ["Keine gültigen Kursdaten für den Historical Runner."]
        n = len(frame)
        if n < self._params.min_history_bars:
            return signals, [f"Zu wenig Historie: {n} < {self._params.min_history_bars} Kerzen."]

        closes = frame[COL_CLOSE].to_numpy(dtype=float)
        timestamps = list(frame.index)
        # Erster Auswertungspunkt: nach dem Vorlauf. Letzter: vorletzte Kerze,
        # damit mindestens eine künftige Kerze zum Simulieren bleibt.
        first = max(self._params.warmup_bars - 1, 1)
        for index in range(first, n - 1, max(self._params.step, 1)):
            window = frame.iloc[: index + 1]
            result = self._runner.run_frame(window, symbol, timeframe)
            signal = self._signal_from_result(result, index, closes, timestamps)
            if signal is not None:
                signals.append(signal)
        if not signals:
            warnings.append("Die Pipeline hat über die Historie keine Empfehlung erzeugt.")
        return signals, warnings

    @staticmethod
    def _signal_from_result(
        result: PipelineResult, index: int, closes: np.ndarray, timestamps: list
    ) -> HistoricalSignal | None:
        """Baut aus einem Pipeline-Ergebnis ein Signal (oder ``None``)."""
        if not result.recommendations.valid:
            return None
        recommendation = result.best()
        if recommendation is None:
            return None
        risk = _risk_for(result, recommendation)
        if risk is None:
            return None

        entry_price = float(closes[index])
        shares = float(risk.estimated_shares)
        stop_distance = float(risk.suggested_stop_distance)
        risk_amount = shares * stop_distance
        timestamp = _as_datetime(timestamps[index])
        return HistoricalSignal(
            bar_index=index,
            timestamp=timestamp,
            entry_price=entry_price,
            direction=recommendation.direction,
            recommendation_strength=recommendation.recommendation_strength,
            suggested_action=recommendation.suggested_action,
            recommendation_id=recommendation.recommendation_id,
            stop_distance=stop_distance,
            take_profit_distance=float(risk.suggested_take_profit),
            shares=shares,
            risk_amount=risk_amount,
            risk_reward=float(risk.suggested_risk_reward),
            commission=float(risk.estimated_commission),
            slippage=float(risk.estimated_slippage),
            reasons=list(recommendation.reasons),
            warnings=list(recommendation.warnings),
        )


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
