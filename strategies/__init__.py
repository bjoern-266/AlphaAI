"""Handelsstrategien (nur Hypothesen, kein Auto-Trading).

Jede Strategie liegt in einer eigenen Datei und ist **unabhängig** von den
anderen Strategien. Eine Strategie kombiniert Indikatoren, Muster und
Marktdaten zu einer objektiven **Hypothese** – sie trifft keine Kauf-/
Verkaufsentscheidung und vergibt keinen Gesamtscore. Die gemeinsame
Schnittstelle und die Ergebnistypen stehen in ``strategies.base``.

Dieses Paket kennt die Engine-Schicht nicht (keine Importe aus ``engines``),
wodurch Import-Zyklen ausgeschlossen sind. Neue Strategien werden über die
Registry (``engines.strategy_registry``) ergänzt.
"""
