"""Projektweite Fehlerklassen für Alpha AI.

Alle fachlichen Fehler von Alpha AI stammen aus **einer** gemeinsamen
Hierarchie mit der Wurzel :class:`AlphaAIError`. Damit kann aufrufender Code
sämtliche Alpha-AI-Fehler gezielt abfangen (``except AlphaAIError``), ohne
breite ``except Exception``-Blöcke zu verwenden.

Grundsatz: **kein blankes** ``ValueError`` / ``KeyError`` für fachliche Fehler.
Statt dessen wird immer eine benannte Klasse dieser Hierarchie ausgelöst. Aus
Gründen der Rückwärtskompatibilität erben einige Klassen zusätzlich von den
eingebauten Ausnahmen (``ValueError`` bzw. ``KeyError``), damit bestehender
Aufrufer-Code mit ``except ValueError`` weiterhin funktioniert. Die **primäre**
Identität bleibt jedoch :class:`AlphaAIError`.
"""

from __future__ import annotations


class AlphaAIError(Exception):
    """Basisklasse für alle von Alpha AI ausgelösten Fehler."""


class ConfigError(AlphaAIError):
    """Wird ausgelöst, wenn die Konfiguration fehlt oder ungültig ist.

    Beispiele: fehlende ``settings.toml``, fehlende Pflichtfelder oder
    Werte außerhalb des zulässigen Bereichs (z. B. negatives Risiko).
    """


class RulesError(AlphaAIError):
    """Basisklasse für Fehler beim Laden fachlicher Regeldateien (TOML)."""


# --------------------------------------------------------------------------- #
# Parameter-Fehler (ungültige/fehlende Fach-Parameter aus den Regeldateien)    #
# --------------------------------------------------------------------------- #


class ParameterError(AlphaAIError, ValueError):
    """Ein fachlicher Parameter fehlt oder ist ungültig.

    Erbt zusätzlich von :class:`ValueError`, damit bestehende
    ``except ValueError``-Erwartungen gültig bleiben.
    """


class IndicatorParameterError(ParameterError):
    """Ein Indikator-Pflichtparameter fehlt oder ist ungültig."""


class PatternParameterError(ParameterError):
    """Ein Muster-Pflichtparameter fehlt oder ist ungültig."""


class StrategyParameterError(ParameterError):
    """Ein Strategie-Pflichtparameter fehlt oder ist ungültig."""


class ScoreParameterError(ParameterError):
    """Score-Gewichte fehlen, sind ungültig oder ergeben ≠ 100 %."""


class RiskParameterError(ParameterError):
    """Risk-Parameter/-Gewichte fehlen, sind ungültig oder ergeben ≠ 100 %."""


# --------------------------------------------------------------------------- #
# Registry-Fehler (Erweiterungsstelle für Plugins)                             #
# --------------------------------------------------------------------------- #


class RegistryError(AlphaAIError):
    """Basisklasse für Fehler einer Plugin-Registry."""


class DuplicateRegistrationError(RegistryError, ValueError):
    """Ein Element mit gleichem Namen ist bereits registriert.

    Erbt zusätzlich von :class:`ValueError` (Rückwärtskompatibilität).
    """


class UnknownComponentError(RegistryError, KeyError):
    """Ein angefragtes Element ist in der Registry nicht registriert.

    Erbt zusätzlich von :class:`KeyError` (Rückwärtskompatibilität).
    """


# --------------------------------------------------------------------------- #
# Cache-Fehler                                                                 #
# --------------------------------------------------------------------------- #


class CacheError(AlphaAIError):
    """Basisklasse für Fehler eines Caches."""


class CacheCapacityError(CacheError, ValueError):
    """Die konfigurierte Cache-Kapazität ist ungültig (< 1).

    Erbt zusätzlich von :class:`ValueError` (Rückwärtskompatibilität).
    """
