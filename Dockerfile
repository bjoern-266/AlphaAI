# AlphaAI Backend – Container für den Dauerbetrieb (Server/Cloud).
#
# Baut ein schlankes Image, das den Backend-Dienst mit echten Marktdaten
# (yfinance) startet und automatisch neu scannt. Ideal für einen kleinen,
# immer laufenden Server (Raspberry Pi, VPS, Cloud-Free-Tier). Das Handy
# braucht dann nur die App.
#
# Bauen & starten:
#   docker build -t alphaai .
#   docker run -p 8000:8000 alphaai
#
# Wichtig für Zugriff vom Handy (nicht nur localhost): in
# knowledge/application_rules.toml unter [api] auth_policy = "open" setzen und
# den Server per Firewall/VPN absichern (der Dienst hat noch keine Tokens).

FROM python:3.12-slim

WORKDIR /app

# Nur die für den Backend-Betrieb nötigen Bibliotheken (kein streamlit/plotly).
RUN pip install --no-cache-dir \
    fastapi "uvicorn[standard]" yfinance pandas numpy pandas-ta

COPY . /app

EXPOSE 8000

# Standard: Nasdaq-100 analysieren, alle 30 Minuten neu scannen.
CMD ["python", "-m", "scripts.serve", "--live", \
     "--universe", "nasdaq100", "--refresh-minutes", "30", \
     "--host", "0.0.0.0", "--port", "8000"]
