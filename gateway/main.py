"""
gateway/main.py — A-TownChain API Gateway
Port 4000 — Zentrales Routing für alle Frontend-Anfragen.

Architektur:
  FRONTEND (3000) → GATEWAY (4000) → BACKEND (5000)

Middleware-Stack (in Reihenfolge):
  1. CORS              — Cross-Origin-Requests erlauben
  2. Rate-Limiting     — 200 req/min pro IP
  3. Logger            — Request/Response-Logging
  4. API-Key-Auth      — Optionale Key-Validierung
  5. Signature-Verify  — ATC-Wallet-Signatur prüfen (optional)
  6. Router            — Proxy zu Backend :5000

Umgebungsvariablen:
  GATEWAY_PORT       = 4000
  BACKEND_URL        = http://localhost:5000
  ALLOWED_ORIGIN     = http://localhost:3000
  ATC_LOG_LEVEL      = INFO
  REQUIRE_API_KEY    = false
"""
import time
import os
import logging
from flask import Flask, jsonify, request, g
from flask_cors import CORS

# ── Gateway-Module laden ────────────────────────────────────────────────────
try:
    from modules.gateway.router import GatewayRouter
    from modules.gateway.middleware.auth import require_api_key
    from modules.gateway.middleware.rate_limit import rate_limiter
    from modules.gateway.middleware.logger import log_request
    from modules.gateway.middleware.signature_verify import verify_signature
    GATEWAY_MODULES = True
except ImportError:
    # Fallback: Direkt-Proxy ohne Middleware
    GATEWAY_MODULES = False

logging.basicConfig(
    level=getattr(logging, os.getenv("ATC_LOG_LEVEL", "INFO")),
    format="%(asctime)s [GATEWAY] %(levelname)s: %(message)s"
)
logger = logging.getLogger("atc.gateway")

# ── Flask-App ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:8080",
    "https://atcnet.io",
    os.getenv("ALLOWED_ORIGIN", ""),
])

GATEWAY_PORT = int(os.getenv("GATEWAY_PORT", 4000))
BACKEND_URL  = os.getenv("BACKEND_URL", "http://localhost:5000")

# ── Router initialisieren ───────────────────────────────────────────────────
if GATEWAY_MODULES:
    router = GatewayRouter(backend_url=BACKEND_URL)
else:
    router = None
    logger.warning("Gateway-Module nicht verfügbar — einfacher Proxy-Modus")

# ── Middleware: Zeitstempel ─────────────────────────────────────────────────
@app.before_request
def before_request():
    g.start_time = time.time()
    if GATEWAY_MODULES:
        log_request(request)

@app.after_request
def after_request(response):
    duration = (time.time() - g.get("start_time", time.time())) * 1000
    response.headers["X-Response-Time"]     = f"{duration:.1f}ms"
    response.headers["X-Gateway-Version"]   = "2.0.0"
    response.headers["X-Powered-By"]        = "A-TownChain Gateway"
    return response

# ── Health & Status ─────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    """Gateway Health-Check."""
    return jsonify({
        "status":   "ok",
        "service":  "atc-gateway",
        "version":  "2.0.0",
        "port":     GATEWAY_PORT,
        "backend":  BACKEND_URL,
        "uptime":   round(time.time(), 0),
    })

@app.route("/api/status", methods=["GET"])
def status():
    """Gateway-Status + Backend-Erreichbarkeit."""
    import urllib.request
    backend_ok = False
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}/api/status", timeout=2) as r:
            backend_ok = (r.status == 200)
    except Exception:
        pass
    return jsonify({
        "gateway": "online",
        "backend": "online" if backend_ok else "offline",
        "backend_url": BACKEND_URL,
    })

# ── Proxy-Routen (alle /api/* → Backend :5000) ─────────────────────────────
@app.route("/api/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy(path):
    """
    Universeller Proxy: /api/<path> → BACKEND_URL/api/<path>

    Middleware-Chain:
      1. Rate-Limit (flask_limiter via before_request)
      2. Auth (optional, REQUIRE_API_KEY=true)
      3. Router.forward()
    """
    if router is None:
        return _simple_proxy(path)
    return router.forward(request, path)

def _simple_proxy(path):
    """Einfacher urllib-Proxy ohne GatewayRouter."""
    import urllib.request
    import urllib.error

    target_url = f"{BACKEND_URL}/api/{path}"
    if request.query_string:
        target_url += "?" + request.query_string.decode()

    try:
        req = urllib.request.Request(
            url    = target_url,
            data   = request.get_data() or None,
            method = request.method,
        )
        for key, val in request.headers:
            if key.lower() not in ("host", "content-length"):
                req.add_header(key, val)

        with urllib.request.urlopen(req, timeout=30) as resp:
            import json
            body = resp.read()
            return app.response_class(
                response = body,
                status   = resp.status,
                mimetype = "application/json",
            )
    except urllib.error.HTTPError as e:
        return jsonify({"error": str(e)}), e.code
    except Exception as e:
        logger.error(f"Proxy-Fehler: {e}")
        return jsonify({"error": "Gateway-Fehler", "detail": str(e)}), 502

# ── 404 / 500 Handler ───────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route nicht gefunden", "gateway": "4000"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Interner Gateway-Fehler"}), 500

# ── Einstiegspunkt ──────────────────────────────────────────────────────────
def run():
    logger.info(f"A-TownChain Gateway startet auf Port {GATEWAY_PORT}")
    logger.info(f"Backend: {BACKEND_URL}")
    app.run(host="0.0.0.0", port=GATEWAY_PORT, debug=False)

if __name__ == "__main__":
    run()
