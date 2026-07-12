"""Ranking-Zusammenbau und Watchlist-Erzeugung.

Nutzt die reinen Bausteine aus :mod:`market_intelligence.ranking`, um bewertete
Chancen zu ordnen (Sortierung + Rangvergabe) und daraus Watchlists abzuleiten. Es
findet **keine** Score-Berechnung statt – nur Ordnen und Auswählen bereits
bewerteter Chancen.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from market_intelligence import ranking
from models.opportunity import Opportunity, Watchlist


def rank(
    opportunities: Sequence[Opportunity], criterion: str = ranking.SORT_SCORE
) -> tuple[Opportunity, ...]:
    """Sortiert die Chancen und vergibt fortlaufende Ränge (1..N)."""
    ordered = ranking.sort_opportunities(opportunities, criterion)
    return ranking.assign_ranks(ordered)


def _watchlist(name: str, title: str, opportunities: Sequence[Opportunity], size: int) -> Watchlist:
    """Baut eine Watchlist aus den ersten ``size`` Tickern (Ranking-Reihenfolge)."""
    tickers = tuple(o.ticker for o in ranking.top(opportunities, size))
    return Watchlist(name=name, title=title, tickers=tickers)


def build_watchlists(
    ranked: Sequence[Opportunity], config: Mapping[str, Any]
) -> dict[str, Watchlist]:
    """Erzeugt die empfohlenen Watchlists (Top / Long / Short).

    Die Größen stammen aus der Regeldatei (``watchlist_*_size``). Die Reihenfolge
    entspricht dem Ranking; es wird **nichts** neu bewertet.
    """
    top_size = int(config.get("watchlist_top_size", 10))
    long_size = int(config.get("watchlist_long_size", 10))
    short_size = int(config.get("watchlist_short_size", 10))
    longs = [o for o in ranked if o.is_long]
    shorts = [o for o in ranked if o.is_short]
    return {
        "top": _watchlist("top", "Top Opportunities", ranked, top_size),
        "long": _watchlist("long", "Long Watchlist", longs, long_size),
        "short": _watchlist("short", "Short Watchlist", shorts, short_size),
    }
