"""Start-Skript des AlphaAI Backend-Dienstes (REST-API über HTTP).

Dieses Skript fährt den produktiven Backend-Dienst hoch und stellt die REST-API
(`/api/v1`) über uvicorn bereit. Es enthält **keine** Fachlogik: es baut die
:class:`~engines.application_engine.ApplicationEngine`, optional lädt es
Demo-Reports (zum sofortigen Ausprobieren) und startet den HTTP-Server.

Beispiele::

    # Mit Demo-Daten starten (sofort etwas sichtbar, ohne echte Marktdaten)
    python -m scripts.serve --demo

    # Nur den Dienst starten (liefert Daten, sobald echte Reports vorliegen)
    python -m scripts.serve --host 0.0.0.0 --port 8000

Hinweis zur Zugriffskontrolle: Standardmäßig erlaubt der Dienst nur lokalen
Zugriff (siehe ``knowledge/application_rules.toml`` → ``[api] auth_policy``).
Für ein physisches Gerät im WLAN dort ``auth_policy = "open"`` setzen.
"""

from __future__ import annotations

import argparse
import threading
import time
from datetime import UTC, datetime
from typing import Any

from application.repositories import ReportStore
from engines.application_engine import ApplicationEngine
from models.application import ReportKind


def seed_demo(store: ReportStore) -> None:
    """Legt Beispiel-Reports an, damit die API/App sofort etwas anzeigt.

    Die Werte sind **Demonstrationsdaten** (keine echte Marktanalyse). Im
    produktiven Betrieb erzeugt der Hintergrunddienst diese Reports automatisch
    aus der bestehenden Analyse-Pipeline.
    """
    now = datetime.now(UTC).isoformat()
    opportunities = [
        _demo_opportunity("NVDA", "NVIDIA", 88.0, "long", "very_high", 0.91, 72.0, 1),
        _demo_opportunity("AAPL", "Apple", 84.0, "long", "high", 0.82, 71.0, 2),
        _demo_opportunity("MSFT", "Microsoft", 79.0, "long", "high", 0.78, 68.0, 3),
        _demo_opportunity("XOM", "Exxon Mobil", 66.0, "short", "medium", 0.61, 55.0, 4, "Energy"),
        _demo_opportunity("TSLA", "Tesla", 63.0, "short", "medium", 0.58, 49.0, 5, "Automotive"),
    ]
    store.save(
        ReportKind.OPPORTUNITIES.value,
        {
            "opportunities": opportunities,
            "statistics": {"analyzed_count": 5, "long_count": 3, "short_count": 2},
        },
        report_version=1,
    )
    store.save(
        ReportKind.DISCOVERY.value,
        {
            "opportunities": opportunities[:3],
            "statistics": {"universe_count": 500, "analyzed_count": 120, "rejected_count": 380},
            "markets": ["nasdaq100", "sp500"],
        },
    )
    store.save(
        ReportKind.OPERATIONS.value,
        {
            "as_of": now,
            "current_session": "USA: open · Europa: geschlossen",
            "market_clock": {
                "as_of": now,
                "markets": [
                    {
                        "key": "us",
                        "title": "USA",
                        "phase": "open",
                        "is_open": True,
                        "next_phase": "close",
                        "seconds_to_next": 5400,
                    },
                    {
                        "key": "europe",
                        "title": "Europa",
                        "phase": "close",
                        "is_open": False,
                        "next_phase": "pre_market",
                        "seconds_to_next": 52200,
                    },
                ],
                "open_markets": ["us"],
                "next_open_market": "europe",
                "next_open_at": now,
            },
            "last_successful_scan_at": now,
            "next_scan_at": now,
            "next_scan_job": "discovery_us",
            "running_job": None,
            "scan_count": 7,
            "error_count": 0,
            "system_state": {
                "health": "ok",
                "heartbeat": {"alive": True, "age_seconds": 4, "interval_seconds": 60},
                "queue_size": 0,
                "scan_count": 7,
                "error_count": 0,
                "uptime_seconds": 4200,
            },
            "new_opportunities": ["NVDA"],
            "new_risks": ["TSLA"],
            "job_history": [
                {
                    "name": "discovery_us",
                    "job_type": "discovery",
                    "status": "success",
                    "duration_seconds": 1.8,
                    "error": "",
                    "summary": "5 Chancen gefunden",
                },
            ],
        },
        report_version=1,
    )


def _demo_opportunity(
    ticker: str,
    company: str,
    score: float,
    direction: str,
    strength: str,
    confidence: float,
    risk: float,
    rank: int,
    sector: str = "Technology",
) -> dict[str, Any]:
    """Baut einen einzelnen Demo-Chancen-Datensatz."""
    return {
        "ticker": ticker,
        "company": company,
        "market": "NASDAQ",
        "sector": sector,
        "direction": direction,
        "recommendation_strength": strength,
        "confidence": confidence,
        "opportunity_score": score,
        "risk": risk,
        "opportunity_rank": rank,
        "summary": f"Demo-Analyse für {company} ({ticker}).",
        "reasons": ["Beispiel-Begründung A", "Beispiel-Begründung B"],
        "warnings": [] if strength != "medium" else ["Erhöhte Volatilität (Demo)"],
        "pattern_summary": "Beispiel-Muster",
        "strategy_summary": "Beispiel-Strategie",
        "analytics_summary": "Beispiel-Analytics",
        "backtest_summary": "Beispiel-Backtest",
        "paper_trading_summary": "Beispiel-Paper-Trading",
    }


def _resolve_symbols(symbols: list[str] | None, universe: str | None) -> list[str] | None:
    """Bestimmt die zu analysierenden Symbole (Symbole > Universum > Konfig)."""
    if symbols:
        return [s.strip().upper() for s in symbols]
    if universe:
        from data.universe import get_universe

        return list(get_universe(universe).symbols)
    return None


def main() -> None:
    """CLI-Einstieg: Engine bauen, Daten laden (Demo oder Live), HTTP-Server starten."""
    parser = argparse.ArgumentParser(description="AlphaAI Backend – REST-API-Server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind-Adresse (Standard: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port (Standard: 8000)")
    parser.add_argument(
        "--demo", action="store_true", help="Demo-Reports laden (ohne echte Marktdaten)"
    )
    parser.add_argument(
        "--live", action="store_true", help="Echte Marktdaten analysieren (Yahoo-Provider)"
    )
    parser.add_argument(
        "--symbols", nargs="+", metavar="TICKER", help="Zu analysierende Symbole (Live-Modus)"
    )
    parser.add_argument(
        "--universe", metavar="KEY", help="Universum analysieren, z. B. 'dax' (Live-Modus)"
    )
    parser.add_argument(
        "--refresh-minutes",
        type=int,
        default=15,
        metavar="N",
        help="Automatischer Neu-Scan alle N Minuten im Live-Modus (0 = aus). Standard: 15.",
    )
    args = parser.parse_args()

    if args.live:
        engine = _build_live_engine(args.symbols, args.universe)
        if args.refresh_minutes > 0:
            _start_refresh_loop(engine, args.refresh_minutes)
    else:
        engine = ApplicationEngine.from_config()
        if args.demo:
            seed_demo(engine.store)
            print("Demo-Reports geladen.")

    app = engine.create_fastapi_app()
    base = f"http://{args.host}:{args.port}/api/v1"
    print(f"AlphaAI Backend läuft auf {base}")
    print(f"Beispiel:  curl {base}/opportunities/top?limit=5")

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


def _start_refresh_loop(engine: ApplicationEngine, minutes: int) -> None:
    """Startet einen Hintergrund-Thread, der alle ``minutes`` neu scannt.

    So läuft der Dienst „von allein": in festem Takt werden erneut echte
    Marktdaten geladen, analysiert und gespeichert. Fehler eines Laufs stoppen
    den Takt nicht – der nächste Lauf versucht es erneut (Recovery).
    """
    interval = minutes * 60

    def loop() -> None:
        while True:
            time.sleep(interval)
            try:
                result = engine.tick()
                stored = ", ".join(result.stored_kinds) or "—"
                print(f"[Auto-Scan] Aktualisiert: {stored}")
            except Exception as error:  # noqa: BLE001 - Takt darf nie hart fehlschlagen
                print(f"[Auto-Scan] Fehler (Dienst läuft weiter): {error}")

    thread = threading.Thread(target=loop, name="alphaai-refresh", daemon=True)
    thread.start()
    print(f"Automatischer Neu-Scan alle {minutes} Minuten aktiv.")


def _build_live_engine(symbols: list[str] | None, universe: str | None) -> ApplicationEngine:
    """Baut die Engine im Live-Modus (echte Marktdaten) und führt den ersten Takt aus."""
    from engines.operations_engine import OperationsEngine
    from scripts.live_backend import LiveBackend

    live = LiveBackend.from_config()
    chosen = _resolve_symbols(symbols, universe)

    # Der Operations-Taktgeber liefert die Marktuhr (ohne echte Jobs auszuführen);
    # die eigentliche Analyse kommt aus der injizierten Report-Quelle.
    operations = OperationsEngine.from_config(jobs={})
    engine = ApplicationEngine.from_config(
        operations=operations,
        report_sources={"opportunities": lambda: live.opportunity_report(chosen)},
    )

    print("Lade echte Marktdaten und analysiere … (kann je nach Anzahl dauern)")
    result = engine.start()
    if result.ok:
        print(f"Analyse abgeschlossen. Gespeichert: {', '.join(result.stored_kinds)}")
    else:
        print(f"Analyse mit Fehlern (Dienst läuft weiter): {result.errors}")
    return engine


if __name__ == "__main__":
    main()
