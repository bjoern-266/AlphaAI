# Strategie-Grundlagen

Diese Datei beschreibt in Worten, wie Alpha AI aus Marktdaten eine
nachvollziehbare Empfehlung ableitet. Die konkreten Parameter stehen in den
TOML-Regeldateien (`indicator_rules.toml`, `pattern_rules.toml`,
`strategy_rules.toml`).

## Ablauf (Zielbild)

1. **Daten laden** – Kursdaten je Symbol über einen Provider beziehen.
2. **Indikatoren berechnen** – Engines erzeugen Kennzahlen (Regeln in
   `indicator_rules.toml`).
3. **Muster erkennen** – Patterns prüfen definierte Kursmuster (Regeln in
   `pattern_rules.toml`).
4. **Setup bewerten** – Strategien kombinieren Indikatoren und Muster zu einer
   Bewertung (Regeln in `strategy_rules.toml`).
5. **Empfehlung erzeugen** – Mit Einstieg, Stop-Loss, Ziel und Begründung.

## Prinzipien

- **Nachvollziehbarkeit vor Komplexität.** Jede Empfehlung muss erklärbar sein.
- **Datengetriebene Regeln.** Schwellenwerte leben in TOML, nicht im Code.
- **Kein Auto-Trading.** Alpha AI empfiehlt, handelt aber nicht selbst.

## Status

Im aktuellen Stand (Sprint 1) ist ausschließlich das Fundament vorhanden.
Die hier beschriebenen Schritte werden in späteren Sprints umgesetzt.
