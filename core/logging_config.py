"""Einheitliche Logging-Konfiguration für Alpha AI.

Alle Module verwenden das Standard-``logging``-Modul und erhalten ihren
Logger über ``logging.getLogger(__name__)``. Die zentrale Einrichtung
erfolgt genau einmal über :func:`setup_logging`.

Es werden zwei Ausgabekanäle konfiguriert:

- Konsole (StreamHandler) – für die interaktive Nutzung.
- Datei (``logs/alpha_ai.log``, rotierend) – für die dauerhafte
  Nachvollziehbarkeit.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from core.paths import LOG_FILE, ensure_runtime_dirs

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Merker, damit Handler nicht mehrfach registriert werden (z. B. bei
# wiederholten Aufrufen in Tests oder beim Neuladen des Dashboards).
_configured: bool = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Richtet das projektweite Logging ein und gibt den Wurzel-Logger zurück.

    Der Aufruf ist idempotent: Mehrfaches Aufrufen fügt keine doppelten
    Handler hinzu, sondern passt nur das Log-Level an.

    Args:
        level: Log-Level für Wurzel-Logger und Handler (Standard: INFO).

    Returns:
        Der konfigurierte Wurzel-Logger.
    """
    global _configured

    ensure_runtime_dirs()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if _configured:
        for handler in root_logger.handlers:
            handler.setLevel(level)
        return root_logger

    formatter = logging.Formatter(fmt=_LOG_FORMAT, datefmt=_DATE_FORMAT)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotierende Datei: max. 1 MB je Datei, 5 Sicherungen.
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    _configured = True
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Gibt einen benannten Logger zurück.

    Dünner Wrapper um :func:`logging.getLogger`, damit Module eine einzige,
    projektspezifische Bezugsquelle für Logger haben.

    Args:
        name: Loggername, üblicherweise ``__name__`` des Aufrufers.

    Returns:
        Der zugehörige :class:`logging.Logger`.
    """
    return logging.getLogger(name)
