"""Cache für Market-Intelligence-Ergebnisse (Re-Export).

Die Definition liegt im Subsystem :mod:`market_intelligence.cache`. Dieses Modul
re-exportiert sie unter dem etablierten Pfad ``engines.market_intelligence_cache``
– konsistent mit ``engines.analytics_cache`` und ``engines.backtest_cache``.
"""

from __future__ import annotations

from market_intelligence.cache import OpportunityCache

__all__ = ["OpportunityCache"]
