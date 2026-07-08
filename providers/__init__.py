"""Datenquellen (Provider).

Kapselt den Zugriff auf externe Marktdaten (z. B. yfinance) hinter einer
einheitlichen Schnittstelle. Durch die Trennung von der Datenschicht lassen
sich Quellen austauschen, ohne abhaengige Module zu aendern (Dependency
Inversion).
"""
