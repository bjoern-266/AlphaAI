"""Chartmuster (Patterns).

Jedes Muster liegt in einer eigenen Datei und ist **vollständig unabhängig**
von den anderen Mustern: Es liest ausschließlich rohe OHLCV-Daten und nie die
Ausgabe eines anderen Musters. Gemeinsame Hilfsmittel (Swing-Erkennung,
Struktur-Break-Erkennung) sowie die Ergebnistypen stehen in ``patterns.base``.

Dieses Paket kennt die Engine-Schicht nicht (keine Importe aus ``engines``),
wodurch Import-Zyklen ausgeschlossen sind. Neue Muster werden über die Registry
(``engines.pattern_registry``) ergänzt.
"""
