"""Live Market Operations Platform (Sprint 16).

Macht AlphaAI zu einem produktiven täglichen Analyse-System: erkennt automatisch
die Marktzeiten, plant die Analyse-Jobs (Market Discovery, Scanner, Analytics, …)
und stellt jederzeit einen belastbaren, **UI-unabhängigen** Systemzustand bereit.

Sie führt **niemals** Orders aus, trifft **keine** Handelsentscheidung und
**berechnet keine** Indikatoren/Muster/Strategien/Scores/Risiken/Empfehlungen –
sie **orchestriert** ausschließlich die bestehende Pipeline (über injizierte
Jobs). Sie importiert nur ``models``/``core`` (keine ``engines`` – kein Zyklus).
"""
