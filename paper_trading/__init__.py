"""Paper-Trading-Framework.

Dieses Paket enthält **keine** neue Handelsregel und **keine** Änderung an den
bestehenden Engines oder am Backtesting-Framework. Es bewertet ausschließlich,
wie sich die **bestehenden** AlphaAI-Empfehlungen unter (simulierten)
Live-Marktbedingungen mit einem **simulierten** Portfolio entwickeln. Es werden
**niemals** echte Orders ausgeführt; es gibt **keine** Broker-Anbindung.

Kette:

``Live-Marktdaten → MarketDataEngine → bestehende Analysepipeline →
RecommendationEngine → PaperTradingEngine → PaperPortfolio → PaperTradingReport``

Bausteine:

* :mod:`paper_trading.order` – Order-Management (OPEN/CLOSE/CANCEL/EXPIRE) und
  Statuswechsel-Validierung,
* :mod:`paper_trading.position` – Positions-Management (Einstieg, Stop,
  Take-Profit, Trailing Stop vorbereitet, Mark-to-Market, Schließen),
* :mod:`paper_trading.portfolio` – das simulierte Portfolio (offene/geschlossene
  Positionen, Kapital, Drawdown, Exposure),
* :mod:`paper_trading.trade` – abgeschlossene Trades,
* :mod:`paper_trading.journal` – automatisches Journal,
* :mod:`paper_trading.statistics` – Handelsstatistik,
* :mod:`paper_trading.performance` – Kapital-/Drawdown-/Exposure-Kennzahlen,
* :mod:`paper_trading.paper_runner` – tägliche Simulation über die bestehende
  Pipeline,
* :mod:`paper_trading.base` – Schnittstelle der Registry-Modelle.

AlphaAI handelt **nicht** automatisch: kein Dashboard, keine Broker-API, keine
echten Orders.
"""
