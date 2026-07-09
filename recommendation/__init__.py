"""Recommendation-Modelle.

Jedes Modell liegt in einer eigenen Datei, ist unabhängig von den anderen und
wird ausschließlich über die ``RecommendationRegistry`` bekannt gemacht.
Gemeinsame Schnittstelle, Faktor-/Rating-/Confidence-Berechnung und die
No-Trade-Gates stehen in ``recommendation/base.py``. Die Modelle erzeugen
objektive, vollständig erklärbare Empfehlungen – keine automatische
Orderausführung, keine Broker-Kommunikation.
"""
