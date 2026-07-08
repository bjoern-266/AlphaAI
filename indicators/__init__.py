"""Technische Indikatoren.

Jeder Indikator liegt in einer eigenen Datei und ist **vollständig unabhängig**
von den anderen Indikatoren: Er liest ausschließlich rohe OHLCV-Daten und nie
die Ausgabe eines anderen Indikators. Die gemeinsame Schnittstelle steht in
``indicators.base``.

Dieses Paket kennt die Engine-Schicht nicht (keine Importe aus ``engines``),
wodurch Import-Zyklen ausgeschlossen sind. Neue Indikatoren werden über die
Registry (``engines.indicator_registry``) ergänzt.
"""
