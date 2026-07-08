"""Repository-Schicht.

Das Repository kapselt sämtliche Provider und ergänzt sie um Cache und
Validierung. Es ist die einzige Schnittstelle, die die
:class:`~data.market_data_engine.MarketDataEngine` kennt. Dadurch bleiben
Provider-Details vollständig hinter dem Repository verborgen.
"""
