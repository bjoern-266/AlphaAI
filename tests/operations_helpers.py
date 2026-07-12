"""Fixtures für die Live-Operations-Tests (Sprint 16)."""

from __future__ import annotations

import copy
from datetime import UTC, datetime

from models.market_discovery import (
    DiscoveryOpportunity,
    DiscoveryReport,
    DiscoveryStatistics,
)
from models.recommendation import Direction, RecommendationStrength

# Minimale, gültige Regel-Struktur (zwei Märkte, kleiner Zeitplan).
RULES_DICT = {
    "meta": {"version": 1},
    "markets": {
        "europe": {
            "title": "Europa",
            "timezone": "Europe/Berlin",
            "phases": [
                ["pre_market", "07:30", False],
                ["open", "09:00", True],
                ["afternoon", "12:00", True],
                ["close", "17:30", False],
            ],
        },
        "us": {
            "title": "USA",
            "timezone": "America/New_York",
            "phases": [
                ["pre_market", "04:00", False],
                ["opening_bell", "09:30", True],
                ["first_hour", "10:30", True],
                ["afternoon", "13:00", True],
                ["close", "16:00", False],
            ],
        },
    },
    "schedule": [
        {
            "name": "europe_open",
            "job_type": "discovery",
            "time": "09:00",
            "timezone": "Europe/Berlin",
        },
        {
            "name": "europe_midday",
            "job_type": "analytics",
            "time": "12:00",
            "timezone": "Europe/Berlin",
        },
        {
            "name": "us_open",
            "job_type": "discovery",
            "time": "09:30",
            "timezone": "America/New_York",
        },
    ],
    "heartbeat": {"interval_seconds": 60},
    "health": {"degraded_ratio": 0.3},
    "history": {"limit": 50},
}


def rules_dict(**overrides) -> dict:
    """Kopie der Standard-Regeln mit optionalen Überschreibungen je Sektion."""
    data = copy.deepcopy(RULES_DICT)
    for section, values in overrides.items():
        data[section] = values
    return data


def make_rules(**overrides):
    """Baut geladene :class:`OperationsRules` aus der Standard-Struktur."""
    from engines.operations_engine import load_operations_rules_from_dict

    return load_operations_rules_from_dict(rules_dict(**overrides))


def make_discovery_report(
    tickers: tuple[str, ...] = ("AAPL", "NVDA"), risky: tuple[str, ...] = ()
) -> DiscoveryReport:
    """Baut einen kleinen DiscoveryReport (für Job-Ergebnisse)."""
    opportunities = tuple(
        DiscoveryOpportunity(
            ticker=ticker,
            company=f"{ticker} Inc",
            sector="Tech",
            country="US",
            exchange="NASDAQ",
            market="sp500",
            direction=Direction.LONG,
            recommendation_strength=RecommendationStrength.HIGH,
            confidence=0.7,
            risk=60.0,
            opportunity_score=90.0 - index,
            rank=index + 1,
            warnings=("Risiko",) if ticker in risky else (),
        )
        for index, ticker in enumerate(tickers)
    )
    return DiscoveryReport(
        opportunities=opportunities,
        statistics=DiscoveryStatistics(universe_count=len(tickers), analyzed_count=len(tickers)),
        valid=True,
    )


def make_engine(clock_time: datetime | None = None, jobs=None, **rule_overrides):
    """Baut eine OperationsEngine mit fester Uhr und injizierten Jobs."""
    from engines.operations_engine import OperationsEngine

    moment = clock_time or datetime(2024, 6, 3, 13, 35, tzinfo=UTC)
    holder = {"now": moment}

    def clock() -> datetime:
        return holder["now"]

    engine = OperationsEngine(
        rules=make_rules(**rule_overrides),
        jobs=jobs if jobs is not None else default_jobs(),
        clock=clock,
    )
    return engine, holder


def default_jobs():
    """Standard-Job-Funktionen (Discovery liefert einen kleinen Report)."""
    return {
        "discovery": lambda: make_discovery_report(),
        "analytics": lambda: "analytics ok",
        "market_intelligence": lambda: "mi ok",
    }
