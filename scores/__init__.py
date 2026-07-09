"""Score-Modelle (objektive Bewertung von Hypothesen).

Jedes Score-Modell liegt in einer eigenen Datei und ist **unabhängig** von den
anderen Modellen. Ein Modell berechnet ausschließlich einen objektiven Score –
es trifft keine Kauf-/Verkaufsentscheidung, erzeugt keine Positionsgröße und
kein Risiko. Die gemeinsame Schnittstelle, die Komponenten-Berechnung und die
Gewichtsvalidierung stehen in ``scores.base``.

Dieses Paket kennt die Engine-Schicht nicht (keine Importe aus ``engines``),
wodurch Import-Zyklen ausgeschlossen sind. Neue Score-Modelle werden über die
Registry (``engines.score_registry``) ergänzt.
"""
