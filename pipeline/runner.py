"""IntegrationRunner – führt einen vollständigen Analyse-Durchlauf aus.

Der :class:`IntegrationRunner` verbindet die bestehenden Engines End-to-End und
liefert ein :class:`~models.pipeline.PipelineResult`. Er enthält **keine**
neue Fachlogik: jede Engine erhält ausschließlich die Ausgaben vorgelagerter
Stufen (Indikatoren/Muster sind gemeinsame Vorstufen, keine Umgehung einer
Schicht). Es findet **keine** Orderausführung und **keine** Broker-Anbindung
statt – am Ende steht ausschließlich eine erklärbare Empfehlung.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from engines.indicator_engine import IndicatorEngine
from engines.pattern_engine import PatternEngine
from engines.recommendation_engine import RecommendationEngine
from engines.risk_engine import RiskEngine
from engines.score_engine import ScoreEngine
from engines.strategy_engine import StrategyEngine
from models.indicator import IndicatorResult
from models.market import MarketResult, MarketStatus
from models.pattern import PatternReport
from models.pipeline import PipelineResult
from models.recommendation import RecommendationReport
from models.risk import OpenPosition, RiskReport
from models.score import ScoreReport
from models.strategy import StrategyReport


class IntegrationRunner:
    """Orchestriert die vollständige AlphaAI-Entscheidungskette.

    Args:
        indicator_engine: Indicator Engine.
        pattern_engine: Pattern Engine.
        strategy_engine: Strategy Engine.
        score_engine: Score Engine.
        risk_engine: Risk Engine.
        recommendation_engine: Recommendation Engine.
    """

    def __init__(
        self,
        indicator_engine: IndicatorEngine,
        pattern_engine: PatternEngine,
        strategy_engine: StrategyEngine,
        score_engine: ScoreEngine,
        risk_engine: RiskEngine,
        recommendation_engine: RecommendationEngine,
    ) -> None:
        self._indicator = indicator_engine
        self._pattern = pattern_engine
        self._strategy = strategy_engine
        self._score = score_engine
        self._risk = risk_engine
        self._recommendation = recommendation_engine

    @classmethod
    def from_config(cls) -> IntegrationRunner:
        """Baut alle Engines aus den Konfigurations-/Regeldateien."""
        return cls(
            indicator_engine=IndicatorEngine.from_config(),
            pattern_engine=PatternEngine.from_config(),
            strategy_engine=StrategyEngine.from_config(),
            score_engine=ScoreEngine.from_config(),
            risk_engine=RiskEngine.from_config(),
            recommendation_engine=RecommendationEngine.from_config(),
        )

    def run(
        self,
        market_result: MarketResult,
        symbol: str,
        timeframe: str = "base",
        open_positions: Sequence[OpenPosition] = (),
    ) -> PipelineResult:
        """Führt die komplette Pipeline für ein Symbol eines MarketResult aus."""
        frame = market_result.frame(symbol)
        if frame is None:
            return self._empty_result(market_result, symbol, timeframe)
        return self._run_frame(market_result, frame, symbol, timeframe, open_positions)

    def run_all(
        self, market_result: MarketResult, timeframe: str = "base"
    ) -> dict[str, PipelineResult]:
        """Führt die Pipeline für alle Symbole eines MarketResult aus."""
        return {
            symbol: self.run(market_result, symbol, timeframe) for symbol in market_result.symbols
        }

    def run_frame(
        self,
        data: pd.DataFrame,
        symbol: str = "SYNTH",
        timeframe: str = "base",
        open_positions: Sequence[OpenPosition] = (),
    ) -> PipelineResult:
        """Führt die Pipeline direkt auf einem OHLCV-DataFrame aus.

        Die Rohdaten werden in ein :class:`MarketResult` verpackt, damit die
        Kette exakt bei der Data Layer beginnt.
        """
        market_result = MarketResult(
            provider="synthetic",
            status=MarketStatus.OK,
            data={symbol.strip().upper(): data},
        )
        return self.run(market_result, symbol, timeframe, open_positions)

    def _run_frame(
        self,
        market_result: MarketResult,
        frame: pd.DataFrame,
        symbol: str,
        timeframe: str,
        open_positions: Sequence[OpenPosition],
    ) -> PipelineResult:
        """Verkettet die sechs Engines; jede erhält nur vorgelagerte Ausgaben."""
        indicators = self._indicator.calculate(frame, symbol, timeframe)
        patterns = self._pattern.detect(frame, symbol, timeframe, indicators=indicators)
        strategies = self._strategy.evaluate(indicators, patterns, frame, symbol, timeframe)
        scores = self._score.score(strategies, indicators, patterns, symbol, timeframe)
        risks = self._risk.assess(scores, indicators, frame, symbol, timeframe, open_positions)
        recommendations = self._recommendation.recommend(
            strategies, scores, risks, symbol, timeframe
        )

        warnings: list[str] = []
        for stage, report in (
            ("indicators", indicators),
            ("patterns", patterns),
            ("strategies", strategies),
            ("scores", scores),
            ("risks", risks),
            ("recommendations", recommendations),
        ):
            warnings.extend(f"[{stage}] {w}" for w in report.warnings)

        metadata = {
            "candle_count": len(frame),
            "indicator_count": len(indicators.outputs),
            "pattern_count": patterns.pattern_count,
            "strategy_count": strategies.hypothesis_count,
            "score_count": scores.score_count,
            "risk_count": risks.risk_count,
            "recommendation_count": recommendations.recommendation_count,
            "all_stages_valid": all(
                r.valid for r in (indicators, patterns, strategies, scores, risks, recommendations)
            ),
        }
        return PipelineResult(
            symbol=symbol,
            timeframe=timeframe,
            market=market_result,
            indicators=indicators,
            patterns=patterns,
            strategies=strategies,
            scores=scores,
            risks=risks,
            recommendations=recommendations,
            warnings=warnings,
            metadata=metadata,
        )

    @staticmethod
    def _empty_result(market_result: MarketResult, symbol: str, timeframe: str) -> PipelineResult:
        """Liefert ein leeres, aber konsistentes Ergebnis bei fehlenden Daten."""
        message = f"Keine Marktdaten für Symbol '{symbol}'."
        return PipelineResult(
            symbol=symbol,
            timeframe=timeframe,
            market=market_result,
            indicators=IndicatorResult(valid=False, warnings=[message]),
            patterns=PatternReport(valid=False, warnings=[message]),
            strategies=StrategyReport(valid=False, warnings=[message]),
            scores=ScoreReport(valid=False, warnings=[message]),
            risks=RiskReport(valid=False, warnings=[message]),
            recommendations=RecommendationReport(valid=False, warnings=[message]),
            warnings=[message],
            metadata={"stage": "no_data", "all_stages_valid": False},
        )
