"""Tests der Live-Verdrahtung (echte Marktdaten → Pipeline → Chancen).

Statt Yahoo wird ein **synthetischer** Provider injiziert (reproduzierbare
Zufalls-OHLCV-Daten). So läuft die vollständige, unveränderte Pipeline durch,
ohne echtes Netzwerk – exakt der Pfad, den ``scripts/serve.py --live`` auf einem
Rechner mit Internet nutzt.
"""

from __future__ import annotations

from datetime import UTC, datetime

import numpy as np
import pandas as pd

from data.market_request import MarketRequest
from models.market import OHLCV_COLUMNS, MarketResult, MarketStatus
from models.recommendation import (
    Direction,
    RecommendationResult,
    RecommendationStrength,
    SuggestedAction,
)
from providers.base_provider import BaseProvider
from scripts.live_backend import LiveBackend, _best_recommendation


class _SyntheticProvider(BaseProvider):
    """Erzeugt reproduzierbare OHLCV-Daten (nur für Tests/Offline-Betrieb)."""

    name = "synthetic"

    def fetch(self, request: MarketRequest) -> MarketResult:
        """Liefert für jedes angefragte Symbol einen deterministischen Frame."""
        data: dict[str, pd.DataFrame] = {}
        for symbol in request.symbols:
            rng = np.random.default_rng(abs(hash(symbol)) % (2**32))
            count = 250
            close = np.maximum(100 + np.cumsum(rng.normal(0.15, 1.5, count)), 5.0)
            frame = pd.DataFrame(
                {
                    "open": close + rng.normal(0, 0.8, count),
                    "high": close + rng.uniform(0.2, 2.0, count),
                    "low": close - rng.uniform(0.2, 2.0, count),
                    "close": close,
                    "adj_close": close,
                    "volume": rng.integers(1_000_000, 5_000_000, count).astype(float),
                },
                index=pd.date_range(end=datetime.now(UTC).date(), periods=count, freq="B"),
            )[list(OHLCV_COLUMNS)]
            data[symbol] = frame
        return MarketResult(provider=self.name, status=MarketStatus.OK, data=data)


def _recommendation(rating: float) -> RecommendationResult:
    """Baut eine minimale Empfehlung mit gegebener Gesamtbewertung."""
    return RecommendationResult(
        recommendation_id="r",
        risk_id="risk",
        score_id="score",
        hypothesis_id="hyp",
        direction=Direction.LONG,
        recommendation_strength=RecommendationStrength.MEDIUM,
        confidence=0.5,
        overall_rating=rating,
        suggested_action=SuggestedAction.MONITOR,
    )


def test_best_recommendation_picks_highest_rating() -> None:
    chosen = _best_recommendation(
        [_recommendation(40.0), _recommendation(80.0), _recommendation(60.0)]
    )
    assert chosen is not None
    assert chosen.overall_rating == 80.0


def test_best_recommendation_empty_returns_none() -> None:
    assert _best_recommendation([]) is None


def test_live_backend_produces_opportunity_report() -> None:
    live = LiveBackend.from_config(provider=_SyntheticProvider())
    report = live.opportunity_report(["AAPL", "MSFT"])
    assert report.valid is True
    assert len(report.opportunities) == 2
    tickers = {opportunity.ticker for opportunity in report.opportunities}
    assert tickers == {"AAPL", "MSFT"}


def test_live_backend_ranks_opportunities() -> None:
    live = LiveBackend.from_config(provider=_SyntheticProvider())
    report = live.opportunity_report(["AAPL", "MSFT", "SPY"])
    ranks = [opportunity.opportunity_rank for opportunity in report.opportunities]
    # Ranking ist 1..n und aufsteigend (Platz 1 zuerst).
    assert ranks == sorted(ranks)
    assert ranks[0] == 1


def test_live_backend_defaults_to_configured_symbols() -> None:
    live = LiveBackend.from_config(provider=_SyntheticProvider())
    report = live.opportunity_report()
    # Ohne Argument werden die in der Konfiguration hinterlegten Märkte genutzt.
    assert len(report.opportunities) >= 1
