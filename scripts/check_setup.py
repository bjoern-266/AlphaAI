"""Prüfskript für das Projektfundament.

Dieses Skript verifiziert, dass die grundlegende Infrastruktur funktioniert:
die Konfiguration lässt sich laden und validieren, und das Logging lässt
sich einrichten. Es enthält bewusst keine Trading- oder Analyselogik.

Aufruf aus dem Projektverzeichnis ``AlphaAI/``::

    python -m scripts.check_setup
"""

from __future__ import annotations

from core.config import load_settings
from core.logging_config import get_logger, setup_logging


def main() -> None:
    """Lädt die Konfiguration, richtet Logging ein und meldet den Status."""
    setup_logging()
    logger = get_logger(__name__)

    settings = load_settings()
    logger.info("Alpha AI Fundament ist einsatzbereit.")
    logger.info(
        "Broker: %s | Depot: %.2f %s",
        settings.account.broker,
        settings.account.capital,
        settings.account.currency,
    )
    logger.info("Risiko pro Trade: %.2f %%", settings.risk.risk_per_trade_pct * 100)
    logger.info("Beobachtete Märkte: %s", ", ".join(settings.markets))


if __name__ == "__main__":
    main()
