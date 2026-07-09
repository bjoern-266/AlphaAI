"""End-to-End-Integration der AlphaAI-Entscheidungskette.

Dieses Paket enthält **keine** neue Fachlogik und **keine** neue Engine. Es
verdrahtet ausschließlich die bestehenden Engines zu einem vollständigen
Analyse-Durchlauf (:class:`pipeline.runner.IntegrationRunner`) und stellt
automatische Konsistenzprüfungen bereit (:mod:`pipeline.consistency`).

Die Kette lautet:

``MarketData → IndicatorEngine → PatternEngine → StrategyEngine → ScoreEngine
→ RiskEngine → RecommendationEngine``

Jede Engine erhält ausschließlich die Ausgaben vorgelagerter Stufen; keine
Engine umgeht eine andere Schicht. Es findet **keine** Orderausführung und
**keine** Broker-Kommunikation statt.
"""
