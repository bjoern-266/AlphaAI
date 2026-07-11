"""Trading Intelligence & Analytics Framework.

Dieses Paket enthält **keine** Handelslogik, **keine** neuen Empfehlungen,
**keine** Machine-Learning-Komponenten und **keine** Änderung an den bestehenden
Engines, am Backtesting oder am Paper Trading. Es **analysiert ausschließlich**
bereits vorhandene Daten aus Backtesting und Paper Trading und erzeugt daraus
**objektive, reproduzierbare Kennzahlen**. Es bewertet **keine** Trades, trifft
**keine** Handelsentscheidung und verändert **keine** bestehenden Ergebnisse.

Kette:

``BacktestReport + PaperTradingReport → AnalyticsEngine → AnalyticsReport``

Bausteine:

* :mod:`analytics.aggregation` – reine, wiederverwendbare Kennzahl-Bausteine
  (Win Rate, Profit Factor, Gruppierung, Drawdown, …),
* :mod:`analytics.labeling` – Ableitung von Dimensionen (Strategie, Risiko-Level,
  Score, Buckets) aus ``recommendation_id``/``reasons`` – vollständig
  nachvollziehbar,
* :mod:`analytics.trade_statistics`, `performance_analyzer`, `pattern_analysis`,
  `strategy_analysis`, `recommendation_analysis`, `risk_analysis`,
  `market_analysis`, `time_analysis`, `journal_analysis`, `summary_analysis` –
  die zehn unabhängigen Analysemodelle (Registry-Plugins),
* :mod:`analytics.base` – Schnittstelle der Analysemodelle.

Alle Kennzahlen werden so bereitgestellt, dass ein späteres Dashboard sie ohne
weitere Berechnung direkt visualisieren kann.
"""
