"""Wiederverwendbare Hilfsfunktionen für die Tests."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

import pandas as pd

from core.config import Settings
from data.market_data_engine import MarketDataEngine
from data.market_result import OHLCV_COLUMNS
from engines.indicator_result import IndicatorResult
from engines.pattern_result import PatternReport
from indicators.base import IndicatorOutput
from patterns.base import PatternDirection, PatternResult, PatternType
from providers.yahoo_provider import DownloadFn, YahooProvider
from repositories.repository_factory import build_repository
from strategies.base import StrategyDirection, StrategyResult


def make_ohlcv(rows: int = 5, start: str = "2024-01-01", freq: str = "D") -> pd.DataFrame:
    """Erzeugt einen gültigen OHLCV-DataFrame im kanonischen Schema.

    Args:
        rows: Anzahl der Zeilen (Kerzen).
        start: Startdatum des Zeitindex.
        freq: Frequenz des Zeitindex (pandas-Offset-Alias).

    Returns:
        DataFrame mit den kanonischen OHLCV-Spalten und DatetimeIndex.
    """
    index = pd.date_range(start=start, periods=rows, freq=freq)
    base = range(1, rows + 1)
    frame = pd.DataFrame(
        {
            "open": [10.0 + i for i in base],
            "high": [11.0 + i for i in base],
            "low": [9.0 + i for i in base],
            "close": [10.5 + i for i in base],
            "adj_close": [10.5 + i for i in base],
            "volume": [1000 + i for i in base],
        },
        index=index,
    )
    return frame[list(OHLCV_COLUMNS)]


def make_yahoo_raw(rows: int = 5, start: str = "2024-01-01") -> pd.DataFrame:
    """Erzeugt einen Roh-DataFrame im yfinance-Format (Spalten wie yfinance)."""
    index = pd.date_range(start=start, periods=rows, freq="D")
    base = range(1, rows + 1)
    return pd.DataFrame(
        {
            "Open": [10.0 + i for i in base],
            "High": [11.0 + i for i in base],
            "Low": [9.0 + i for i in base],
            "Close": [10.5 + i for i in base],
            "Adj Close": [10.4 + i for i in base],
            "Volume": [1000 + i for i in base],
        },
        index=index,
    )


class FakeClock:
    """Kontrollierbare Uhr für zeitabhängige Tests."""

    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        """Rückt die Uhr um die angegebene Sekundenzahl vor."""
        self._now += seconds


def make_price_frame(
    closes: list[float],
    highs: list[float] | None = None,
    lows: list[float] | None = None,
    opens: list[float] | None = None,
    volume: list[float] | None = None,
    start: str = "2023-01-01",
    freq: str = "D",
) -> pd.DataFrame:
    """Baut einen OHLCV-DataFrame im kanonischen Schema aus Schlusskursen.

    High/Low/Open/Volume werden – falls nicht angegeben – aus den Schlusskursen
    abgeleitet (High = Close + 1, Low = Close - 1, Open = Close, Volume = 1000).
    """
    n = len(closes)
    index = pd.date_range(start=start, periods=n, freq=freq)
    return pd.DataFrame(
        {
            "open": [float(v) for v in (opens if opens is not None else closes)],
            "high": [float(v) for v in (highs if highs is not None else [c + 1 for c in closes])],
            "low": [float(v) for v in (lows if lows is not None else [c - 1 for c in closes])],
            "close": [float(v) for v in closes],
            "adj_close": [float(v) for v in closes],
            "volume": [float(v) for v in (volume if volume is not None else [1000.0] * n)],
        },
        index=index,
    )


def make_engine(
    download_fn: DownloadFn,
    settings: Settings,
    clock: Callable[[], float],
    universe_resolver: Callable | None = None,
) -> MarketDataEngine:
    """Baut einen echten, aber netzwerkfreien MarketDataEngine.

    Nutzt den realen Repository-/Cache-/Validator-Stack mit einem
    YahooProvider, dessen Download-Funktion injiziert ist.
    """
    provider = YahooProvider(download_fn=download_fn)
    repository = build_repository(settings, provider=provider, clock=clock)
    return MarketDataEngine(repository, settings, universe_resolver=universe_resolver)


def _one(value: float) -> pd.Series:
    """Einelementige Serie (für Test-Indikatorwerte)."""
    return pd.Series([float(value)])


def make_indicator_result(
    ema: dict[int, float] | None = None,
    rsi: float | None = None,
    atr: float | None = None,
    adx: float | None = None,
    macd: dict[str, float] | None = None,
    relative_volume: float | None = None,
    bollinger: dict[str, float] | None = None,
    valid: bool = True,
    candle_count: int = 260,
    timeframe: str = "base",
) -> IndicatorResult:
    """Baut ein IndicatorResult mit gezielt gesetzten letzten Werten (für Tests)."""
    outputs: dict[str, IndicatorOutput] = {}
    if ema is not None:
        outputs["ema"] = IndicatorOutput(
            name="ema", series={f"ema_{p}": _one(v) for p, v in ema.items()}
        )
    if rsi is not None:
        outputs["rsi"] = IndicatorOutput(name="rsi", series={"rsi_14": _one(rsi)})
    if atr is not None:
        outputs["atr"] = IndicatorOutput(name="atr", series={"atr_14": _one(atr)})
    if adx is not None:
        outputs["adx"] = IndicatorOutput(name="adx", series={"adx": _one(adx)})
    if macd is not None:
        outputs["macd"] = IndicatorOutput(name="macd", series={k: _one(v) for k, v in macd.items()})
    if relative_volume is not None:
        outputs["relative_volume"] = IndicatorOutput(
            name="relative_volume", series={"relative_volume": _one(relative_volume)}
        )
    if bollinger is not None:
        outputs["bollinger"] = IndicatorOutput(
            name="bollinger", series={k: _one(v) for k, v in bollinger.items()}
        )
    return IndicatorResult(
        outputs=outputs,
        valid=valid,
        metadata={"candle_count": candle_count, "timeframe": timeframe, "rules_version": 2},
    )


def make_pattern_result(
    name: str,
    direction: PatternDirection = PatternDirection.BULLISH,
    strength: float = 50.0,
    confidence: float = 0.6,
    price_level: float = 100.0,
    timestamp: datetime | None = None,
    fresh: bool = True,
    pattern_type: PatternType = PatternType.FAIR_VALUE_GAP,
) -> PatternResult:
    """Baut ein einzelnes PatternResult (für Tests)."""
    return PatternResult(
        name=name,
        pattern_type=pattern_type,
        direction=direction,
        strength=strength,
        confidence=confidence,
        timestamp=timestamp or datetime(2024, 1, 1, tzinfo=UTC),
        price_level=price_level,
        metadata={"fresh": fresh},
    )


def make_pattern_report(
    results: list[PatternResult] | None = None,
    valid: bool = True,
    candle_count: int = 260,
    timeframe: str = "base",
) -> PatternReport:
    """Baut ein PatternReport mit gegebenen Ergebnissen (für Tests)."""
    return PatternReport(
        results=results or [],
        valid=valid,
        metadata={"candle_count": candle_count, "timeframe": timeframe, "rules_version": 2},
    )


def make_strategy_result(
    strategy_name: str = "strat",
    direction: StrategyDirection | None = None,
    confidence: float = 0.6,
    strength: float = 50.0,
    matched_indicators: list[str] | None = None,
    matched_patterns: list[str] | None = None,
    hypothesis_id: str | None = None,
    timestamp: datetime | None = None,
) -> StrategyResult:
    """Baut ein StrategyResult (für Score-Tests)."""
    direction = direction or StrategyDirection.BULLISH
    return StrategyResult(
        strategy_name=strategy_name,
        hypothesis_id=hypothesis_id or f"{strategy_name}:{direction.value}:na",
        direction=direction,
        confidence=confidence,
        strength=strength,
        matched_indicators=matched_indicators or [],
        matched_patterns=matched_patterns or [],
        timestamp=timestamp or datetime(2024, 1, 1, tzinfo=UTC),
    )


def make_components(**overrides: float):
    """Baut die acht Score-Komponenten mit gegebenen Werten (Standard 50)."""
    from scores.base import COMPONENT_NAMES, ComponentScore

    return {
        name: ComponentScore(name, float(overrides.get(name, 50.0)), f"{name}: test")
        for name in COMPONENT_NAMES
    }


def make_score_context(
    strategy_result=None,
    components=None,
    hypotheses=None,
    indicators=None,
    patterns=None,
):
    """Baut einen ScoreContext (für Score-Modell-Tests)."""
    from scores.base import ScoreContext

    sr = strategy_result or make_strategy_result()
    return ScoreContext(
        strategy_result=sr,
        indicators=indicators or make_indicator_result(),
        patterns=patterns or make_pattern_report(),
        hypotheses=hypotheses or [sr],
        components=components or make_components(),
    )


def make_account(capital: float = 10000.0, fractional: bool = True):
    """Baut eine AccountConfig (für Risk-Tests)."""
    from core.config import AccountConfig

    return AccountConfig(
        capital=capital, currency="EUR", broker="Test", fractional_shares=fractional
    )


def make_risk_config(
    risk_per_trade_pct: float = 0.01, max_open_positions: int = 5, max_daily_loss_pct: float = 0.03
):
    """Baut eine RiskConfig (für Risk-Tests)."""
    from core.config import RiskConfig

    return RiskConfig(
        risk_per_trade_pct=risk_per_trade_pct,
        max_open_positions=max_open_positions,
        max_daily_loss_pct=max_daily_loss_pct,
    )


def make_settings(capital: float = 10000.0, fractional: bool = True, **risk_kwargs):
    """Baut vollständige Settings (für die RiskEngine)."""
    from core.config import (
        CacheConfig,
        DataConfig,
        ScannerConfig,
        Settings,
        TradingHoursConfig,
    )

    return Settings(
        account=make_account(capital=capital, fractional=fractional),
        risk=make_risk_config(**risk_kwargs),
        trading_hours=TradingHoursConfig("Europe/Berlin", "09:00", "17:30"),
        data=DataConfig("yahoo", "1d", "6mo", CacheConfig(True, 86400, 300, 604800)),
        scanner=ScannerConfig(4, ("indicators",)),
        markets=["AAPL"],
    )


def make_score_result(
    score_id: str = "score:h1",
    hypothesis_id: str = "h1",
    strategy_name: str = "strat",
    total_score: float = 70.0,
    confidence: float = 0.6,
    quality_score: float = 80.0,
    consensus_score: float = 60.0,
    market_score: float = 60.0,
    data_quality: float = 100.0,
    timestamp: datetime | None = None,
):
    """Baut ein ScoreResult (für Risk-Tests)."""
    from models.score import COMPONENT_NAMES, ScoreResult

    component_scores = {name: 50.0 for name in COMPONENT_NAMES}
    component_scores["data_quality"] = data_quality
    return ScoreResult(
        score_id=score_id,
        strategy_name=strategy_name,
        hypothesis_id=hypothesis_id,
        total_score=total_score,
        confidence=confidence,
        quality_score=quality_score,
        consensus_score=consensus_score,
        market_score=market_score,
        component_scores=component_scores,
        timestamp=timestamp or datetime(2024, 1, 1, tzinfo=UTC),
    )


def make_score_report(results=None, valid: bool = True, candle_count: int = 60):
    """Baut ein ScoreReport (für die RiskEngine)."""
    from models.score import ScoreReport

    return ScoreReport(
        results=results if results is not None else [make_score_result()],
        valid=valid,
        metadata={"candle_count": candle_count, "timeframe": "base"},
    )


def make_risk_context(
    atr: float | None = 2.0,
    market_score: float = 60.0,
    data_quality: float = 100.0,
    capital: float = 10000.0,
    fractional: bool = True,
    rows: int = 60,
    volume: float = 1_000_000.0,
    price_data=None,
    open_positions=(),
    risk_per_trade_pct: float = 0.01,
    max_open_positions: int = 5,
):
    """Baut einen RiskContext (für Risk-Modell-Tests)."""
    from models.risk import RiskContext

    if price_data is None:
        closes = [100.0 + i * 0.2 for i in range(rows)]
        price_data = make_price_frame(closes, volume=[volume] * rows)
    indicators = make_indicator_result(atr=atr, candle_count=rows)
    score = make_score_result(market_score=market_score, data_quality=data_quality)
    return RiskContext(
        score_result=score,
        indicators=indicators,
        account=make_account(capital=capital, fractional=fractional),
        risk=make_risk_config(
            risk_per_trade_pct=risk_per_trade_pct, max_open_positions=max_open_positions
        ),
        data=price_data,
        open_positions=open_positions,
        symbol="AAPL",
        timeframe="base",
    )


def make_risk_result(
    hypothesis_id: str = "h1",
    score_id: str | None = None,
    overall_risk: float = 20.0,
    risk_level=None,
    risk_components: dict[str, float] | None = None,
    timestamp: datetime | None = None,
):
    """Baut ein RiskResult (für Recommendation-Tests)."""
    from models.risk import RiskLevel, RiskResult

    score_id = score_id or f"score:{hypothesis_id}"
    return RiskResult(
        risk_id=f"risk:{score_id}",
        score_id=score_id,
        hypothesis_id=hypothesis_id,
        overall_risk=overall_risk,
        risk_level=risk_level or RiskLevel.LOW,
        suggested_position_size=2000.0,
        maximum_risk_pct=1.0,
        maximum_portfolio_exposure=10000.0,
        estimated_shares=17.0,
        estimated_order_value=2000.0,
        estimated_slippage=1.0,
        estimated_commission=2.0,
        suggested_stop_distance=4.0,
        suggested_take_profit=8.0,
        suggested_risk_reward=2.0,
        risk_components=risk_components or {"gap": 10.0, "volatility": 10.0, "data_quality": 0.0},
        timestamp=timestamp or datetime(2024, 1, 1, tzinfo=UTC),
    )


def make_risk_report(results=None, valid: bool = True):
    """Baut ein RiskReport (für die RecommendationEngine)."""
    from models.risk import RiskReport

    return RiskReport(
        results=results if results is not None else [make_risk_result()],
        valid=valid,
        metadata={"timeframe": "base"},
    )


# Standardgewichte (spiegeln knowledge/recommendation_rules.toml) für Kontext-Bau.
_REC_FACTOR_WEIGHTS = {
    "strategy": 0.15,
    "score": 0.25,
    "risk": 0.20,
    "consensus": 0.20,
    "market_quality": 0.10,
    "data_quality": 0.10,
}
_REC_CONFIDENCE_WEIGHTS = {
    "strategy_confidence": 0.35,
    "consensus": 0.30,
    "risk": 0.20,
    "data_quality": 0.15,
}


def make_recommendation_context(
    strategy_result=None,
    score_result=None,
    risk_result=None,
    strategies=None,
    consensus_full_at: int = 2,
    symbol: str = "AAPL",
):
    """Baut einen RecommendationContext mit vorab berechneten Faktoren/Rating/Confidence."""
    from models.recommendation import RecommendationContext
    from recommendation.base import (
        compute_confidence,
        compute_factors,
        compute_overall_rating,
    )

    strat = strategy_result or make_strategy_result()
    score = score_result or make_score_result(hypothesis_id=strat.hypothesis_id)
    risk = risk_result or make_risk_result(hypothesis_id=strat.hypothesis_id)
    all_strategies = strategies if strategies is not None else [strat]
    factors = compute_factors(
        strat, score, risk, all_strategies, consensus_full_at=consensus_full_at
    )
    overall_rating = compute_overall_rating(factors, _REC_FACTOR_WEIGHTS)
    base_confidence = compute_confidence(strat, factors, _REC_CONFIDENCE_WEIGHTS)
    return RecommendationContext(
        strategy_result=strat,
        score_result=score,
        risk_result=risk,
        strategies=all_strategies,
        factors=factors,
        overall_rating=overall_rating,
        base_confidence=base_confidence,
        symbol=symbol,
        timeframe="base",
    )


# --------------------------------------------------------------------------- #
# Backtesting-Helfer (Sprint 10)                                              #
# --------------------------------------------------------------------------- #

# Standard-Backtestregeln mit kleinem Vorlauf für schnelle Engine-Tests.
_BACKTEST_RULES_FAST = {
    "meta": {"version": 1},
    "engine": {"warmup_bars": 30, "step": 5, "min_history_bars": 30},
    "simulation": {"max_holding_bars": 10, "apply_costs": True, "breakeven_epsilon": 0.01},
    "performance_model": {"enabled": True},
    "drawdown_model": {"enabled": True},
    "ratio_model": {"enabled": True, "risk_free_rate": 0.0, "periods_per_year": 0},
    "benchmark_model": {"enabled": True},
}


def make_backtest_rules(**overrides):
    """Baut BacktestRules mit kleinem Vorlauf (für schnelle Engine-Tests)."""
    import copy

    from engines.backtest_engine import load_backtest_rules_from_dict

    data = copy.deepcopy(_BACKTEST_RULES_FAST)
    for section, values in overrides.items():
        if isinstance(values, dict):
            data.setdefault(section, {}).update(values)
        else:
            data[section] = values
    return load_backtest_rules_from_dict(data)


def make_trend_frame(
    n: int = 60, base: float = 100.0, slope: float = 0.5, start: str = "2023-01-01"
):
    """Baut einen kanonischen OHLCV-Aufwärtstrend mit DatetimeIndex."""
    import numpy as np

    closes = base + slope * np.arange(n)
    return make_price_frame(list(closes), volume=[1_000_000.0] * n, start=start)


def make_historical_signal(
    bar_index: int = 5,
    direction=None,
    strength=None,
    action=None,
    entry_price: float = 100.0,
    stop_distance: float = 2.0,
    take_profit_distance: float = 4.0,
    shares: float = 10.0,
    risk_reward: float = 2.0,
    commission: float = 1.0,
    slippage: float = 0.5,
    timestamp: datetime | None = None,
):
    """Baut ein HistoricalSignal (für Trade-Simulator-Tests)."""
    from models.backtest import HistoricalSignal
    from models.recommendation import Direction, RecommendationStrength, SuggestedAction

    direction = direction or Direction.LONG
    strength = strength or RecommendationStrength.VERY_HIGH
    action = action or SuggestedAction.OPEN
    return HistoricalSignal(
        bar_index=bar_index,
        timestamp=timestamp or datetime(2023, 1, 1, tzinfo=UTC),
        entry_price=entry_price,
        direction=direction,
        recommendation_strength=strength,
        suggested_action=action,
        recommendation_id=f"rec:{bar_index}",
        stop_distance=stop_distance,
        take_profit_distance=take_profit_distance,
        shares=shares,
        risk_amount=shares * stop_distance,
        risk_reward=risk_reward,
        commission=commission,
        slippage=slippage,
        reasons=["Testgrund"],
        warnings=[],
    )


def make_simulated_trade(
    trade_id: str = "bt:AAPL:5",
    symbol: str = "AAPL",
    direction=None,
    strength=None,
    profit: float = 100.0,
    risk_amount: float = 20.0,
    risk_reward: float = 2.0,
    holding_bars: int = 3,
    position_value: float = 1000.0,
    outcome=None,
    exit_reason=None,
    entry_time: datetime | None = None,
    exit_time: datetime | None = None,
):
    """Baut ein SimulatedTrade (für Kennzahl-/Kurven-Tests)."""
    from datetime import timedelta

    from models.backtest import ExitReason, SimulatedTrade, TradeOutcome
    from models.recommendation import Direction, RecommendationStrength

    direction = direction or Direction.LONG
    strength = strength or RecommendationStrength.HIGH
    if outcome is None:
        outcome = (
            TradeOutcome.WIN
            if profit > 0
            else TradeOutcome.LOSS if profit < 0 else TradeOutcome.BREAKEVEN
        )
    entry_time = entry_time or datetime(2023, 1, 1, tzinfo=UTC)
    exit_time = exit_time or (entry_time + timedelta(days=holding_bars))
    return SimulatedTrade(
        trade_id=trade_id,
        symbol=symbol,
        direction=direction,
        recommendation_strength=strength,
        recommendation_id="rec:x",
        entry_time=entry_time,
        entry_price=100.0,
        exit_time=exit_time,
        exit_price=100.0 + profit / 10.0,
        stop_price=98.0,
        take_profit_price=104.0,
        shares=10.0,
        risk_amount=risk_amount,
        position_value=position_value,
        profit=profit,
        profit_pct=(profit / position_value * 100.0) if position_value else 0.0,
        return_on_risk=(profit / risk_amount) if risk_amount else 0.0,
        risk_reward=risk_reward,
        holding_bars=holding_bars,
        holding_time=exit_time - entry_time,
        outcome=outcome,
        exit_reason=exit_reason or ExitReason.TAKE_PROFIT,
        commission=1.0,
        slippage=0.5,
        reasons=["Testgrund"],
        warnings=[],
    )
