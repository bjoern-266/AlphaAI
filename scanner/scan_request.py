"""Anfrageobjekt für einen Scan-Lauf.

Ein :class:`ScanRequest` beschreibt unveränderlich, was gescannt werden soll.
Der Scanner Core führt keinerlei Analyse aus; ``requested_features`` und
``max_workers`` werden lediglich mitgeführt und sind für spätere Sprints
vorbereitet.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.config import Settings
from core.exceptions import AlphaAIError


class InvalidScanRequestError(AlphaAIError):
    """Wird ausgelöst, wenn ein :class:`ScanRequest` unzulässig ist."""


@dataclass(frozen=True, slots=True)
class ScanRequest:
    """Beschreibt einen Scan-Lauf.

    Es muss entweder ``universe`` oder ``symbols`` (oder beides) angegeben sein.

    Attributes:
        market: Bezeichnung des Marktes (frei, z. B. ``"dax"``, ``"usa"``).
        universe: Optionaler Universumsschlüssel (z. B. ``"dax"``), der zu
            Symbolen aufgelöst wird.
        symbols: Zusätzliche explizite Symbole. Werden normalisiert (getrimmt,
            Großschreibung, dedupliziert).
        provider: Gewünschter Provider (nur festgehalten; die tatsächliche
            Datenquelle stellt die Data Layer bereit). ``None`` = Standard.
        timeframe: Zeitraum/Rückschau. ``None`` = Standard aus Konfiguration.
        interval: Kerzenintervall. ``None`` = Standard aus Konfiguration.
        use_cache: Ob der Cache verwendet werden darf.
        requested_features: Später anzuwendende Analysebausteine (nur mitgeführt).
        max_workers: Vorbereitete Worker-Anzahl (aktuell ohne Parallelisierung).
    """

    market: str
    universe: str | None = None
    symbols: tuple[str, ...] = ()
    provider: str | None = None
    timeframe: str | None = None
    interval: str | None = None
    use_cache: bool = True
    requested_features: tuple[str, ...] = ()
    max_workers: int = 1

    def __post_init__(self) -> None:
        """Normalisiert und validiert die Felder nach der Initialisierung."""
        object.__setattr__(self, "market", self.market.strip())
        object.__setattr__(self, "symbols", _normalize_symbols(self.symbols))
        object.__setattr__(
            self,
            "requested_features",
            tuple(f.strip().lower() for f in self.requested_features if f and f.strip()),
        )
        universe = self.universe.strip() if self.universe else None
        object.__setattr__(self, "universe", universe or None)

        if not self.market:
            raise InvalidScanRequestError("ScanRequest benötigt einen Markt (market).")
        if not self.universe and not self.symbols:
            raise InvalidScanRequestError(
                "ScanRequest benötigt entweder ein Universum oder mindestens ein Symbol."
            )
        if self.max_workers < 1:
            raise InvalidScanRequestError("max_workers muss mindestens 1 sein.")


def _normalize_symbols(symbols: tuple[str, ...]) -> tuple[str, ...]:
    """Trimmt, vereinheitlicht die Groß-/Kleinschreibung und dedupliziert."""
    seen: dict[str, None] = {}
    for symbol in symbols:
        if symbol and symbol.strip():
            seen[symbol.strip().upper()] = None
    return tuple(seen)


def build_scan_request(
    settings: Settings,
    market: str,
    universe: str | None = None,
    symbols: tuple[str, ...] | list[str] = (),
    provider: str | None = None,
    timeframe: str | None = None,
    interval: str | None = None,
    use_cache: bool = True,
    requested_features: tuple[str, ...] | list[str] | None = None,
    max_workers: int | None = None,
) -> ScanRequest:
    """Erzeugt einen :class:`ScanRequest` und füllt Standards aus der Konfiguration.

    ``requested_features`` und ``max_workers`` werden aus ``settings.scanner``
    übernommen, wenn sie nicht explizit angegeben sind. So bleiben diese Werte
    frei von Hardcodes.

    Args:
        settings: Geladene Projektkonfiguration.
        market: Marktbezeichnung.
        universe: Optionaler Universumsschlüssel.
        symbols: Zusätzliche explizite Symbole.
        provider: Gewünschter Provider.
        timeframe: Zeitraum/Rückschau.
        interval: Kerzenintervall.
        use_cache: Ob der Cache verwendet werden darf.
        requested_features: Analysebausteine (Standard aus Konfiguration).
        max_workers: Worker-Anzahl (Standard aus Konfiguration).

    Returns:
        Ein validierter :class:`ScanRequest`.
    """
    features = (
        tuple(requested_features)
        if requested_features is not None
        else settings.scanner.requested_features
    )
    workers = max_workers if max_workers is not None else settings.scanner.max_workers
    return ScanRequest(
        market=market,
        universe=universe,
        symbols=tuple(symbols),
        provider=provider,
        timeframe=timeframe,
        interval=interval,
        use_cache=use_cache,
        requested_features=features,
        max_workers=workers,
    )
