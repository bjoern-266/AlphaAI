#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
# AlphaAI – Ein-Klick-Setup für Android (Termux)
# =============================================================================
# Installiert AlphaAI direkt auf dem Handy und startet den Backend-Dienst mit
# echten Marktdaten (yfinance) und automatischem Neu-Scan. Danach zeigt die App
# (Backend-Adresse: http://127.0.0.1:8000/) laufend die aktuellen Vorschläge.
#
# So benutzt du es:
#   1. Termux aus F-Droid installieren (nicht aus dem Play Store).
#   2. Dieses Skript in Termux ausführen:
#        curl -sL <URL-zu-dieser-Datei> -o setup.sh && bash setup.sh
#      (oder Datei kopieren und `bash termux_setup.sh`)
#
# Hinweis: Termux/Android kann Abhängigkeiten auf ARM zickig machen. Bei
# Problemen ist der Server-Weg (siehe Dockerfile) zuverlässiger.
# =============================================================================
set -e

# Repo-Adresse (Mirror mit dem Code in der Wurzel). Bei privatem Repo ggf.
# einen Personal Access Token in der URL verwenden.
REPO_URL="${ALPHAAI_REPO:-https://github.com/bjoern-266/AlphaAI.git}"
UNIVERSE="${ALPHAAI_UNIVERSE:-nasdaq100}"
REFRESH="${ALPHAAI_REFRESH:-30}"

echo "== 1/5  Hält das Handy für den Dienst wach =="
termux-wake-lock 2>/dev/null || true

echo "== 2/5  Systempakete (Python, numpy, pandas, git) =="
pkg update -y && pkg upgrade -y
# numpy/pandas als vorgebaute Termux-Pakete – vermeidet langes Kompilieren.
pkg install -y python git python-numpy python-pandas

echo "== 3/5  Python-Bibliotheken (API, Marktdaten) =="
pip install --upgrade pip wheel
# Schlankes uvicorn (ohne uvloop-Kompilierung); Analyse-Zusatz ohne Zwangs-Deps.
pip install fastapi uvicorn yfinance
pip install --no-deps pandas-ta || echo "  (pandas-ta optional – Dienst läuft auch ohne)"

echo "== 4/5  AlphaAI-Code holen =="
if [ ! -d AlphaAI ]; then
    git clone --depth 1 "$REPO_URL" AlphaAI
fi
cd AlphaAI

echo "== 5/5  Start: echte Marktdaten, Auto-Scan alle ${REFRESH} Min =="
echo "   In der App die Backend-Adresse setzen:  http://127.0.0.1:8000/"
echo "   Beenden mit  Strg+C.  Neustart:  cd AlphaAI && python -m scripts.serve --live --universe ${UNIVERSE} --refresh-minutes ${REFRESH}"
exec python -m scripts.serve --live --universe "$UNIVERSE" --refresh-minutes "$REFRESH" --host 127.0.0.1 --port 8000
