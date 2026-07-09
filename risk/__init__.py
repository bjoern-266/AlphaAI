"""Risikomodelle.

Jedes Risk-Modell liegt in einer eigenen Datei, ist unabhängig von den anderen
und wird ausschließlich über die ``RiskRegistry`` bekannt gemacht. Gemeinsame
Schnittstelle, Positionsgrößen-Berechnung und Komponenten-Hilfsmittel stehen in
``risk/base.py``. Die Modelle bewerten Risiko objektiv – sie treffen keine
Kauf-/Verkaufsentscheidung und erzeugen keine Orders.
"""
