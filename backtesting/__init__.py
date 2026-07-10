"""Historisches Backtesting-Framework.

Dieses Paket enthält **keine** neue Handelsregel und **keine** Änderung an den
bestehenden Engines. Es lässt historische Marktdaten durch die **bestehende**
AlphaAI-Pipeline laufen und bewertet objektiv, wie sich die daraus entstehenden
Empfehlungen entwickelt hätten. Es werden **keine** echten Orders ausgeführt;
Trades werden ausschließlich rechnerisch simuliert.

Kette:

``Historische Marktdaten → MarketDataEngine → IndicatorEngine → PatternEngine →
StrategyEngine → ScoreEngine → RiskEngine → RecommendationEngine → BacktestEngine
→ BacktestReport``

Bausteine:

* :mod:`backtesting.historical_runner` – führt die Pipeline zeitpunktweise über
  die Historie aus und sammelt die Empfehlungen als Signale,
* :mod:`backtesting.trade_simulator` – simuliert aus den Signalen Trades
  (Einstieg/Ausstieg/Stop/Take-Profit), Fractional Shares, Risiko aus
  ``settings.toml``,
* :mod:`backtesting.performance_metrics` – Kennzahlen (Win Rate, Profit Factor,
  Expectancy, …),
* :mod:`backtesting.equity_curve` – Kapitalkurve und Drawdown,
* :mod:`backtesting.statistics` – risikoadjustierte Kennzahlen (vorbereitet),
* :mod:`backtesting.benchmark` – Vergleichsmaßstäbe (z. B. Buy & Hold),
* :mod:`backtesting.base` – gemeinsame Schnittstelle der Backtest-Modelle.

AlphaAI handelt **nicht** automatisch: kein Dashboard, keine Broker-API, kein
Paper-Trading, keine Orderausführung.
"""
