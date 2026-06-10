"""
A-TownChain API Gateway v2.0.0
Port 4000 — Zentrales Routing für alle Frontend-Anfragen.

Architektur:
  FRONTEND (3000) → GATEWAY (4000) → BACKEND (5000)
"""
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from gateway.router import GatewayRouter
from gateway.middleware.auth import require_api_key
from gateway.middleware.rate_limit import rate_limiter
from gateway.middleware.logger import log_request
from gateway.middleware.signature_verify import verify_signature
import time, os, logging

logging.basicConfig(
    level=getattr(logging, os.getenv("ATC_LOG_LEVEL", "INFO")),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("atc.gateway")

app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:8080",
    "https://atcnet.io",
    os.getenv("ALLOWED_ORIGIN", ""),
])

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per minute", "2000 per hour"],
    storage_uri="memory://",
)

router = GatewayRouter(
    backend_url=os.getenv("BACKEND_URL", "http://localhost:5000")
)

# ── Middleware ─────────────────────────────────────
@app.before_request
def before():
    g.start_time = time.time()
    log_request(request)

@app.after_request
def after(response):
    duration = (time.time() - g.get("start_time", time.time())) * 1000
    response.headers["X-Response-Time"] = f"{duration:.1f}ms"
    response.headers["X-Gateway-Version"] = "2.0.0"
    return response

# ── Health ─────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "version": "2.0.0",
        "services": router.check_backend(),
        "ts": time.time(),
    })

@app.route("/api/status")
def status():
    return jsonify({"gateway": "online", "version": "2.0.0"})

# ── API Routes ─────────────────────────────────────
@app.route("/api/<path:path>", methods=["GET","POST","PUT","DELETE","PATCH"])
@require_api_key
@limiter.limit("100 per minute")
def proxy(path):
    return router.forward(request, path)

# ── Metrics (Prometheus) ───────────────────────────
@app.route("/metrics")
def metrics():
    stats = router.stats()
    lines = [
        "# HELP atc_gateway_requests_total Total requests",
        "# TYPE atc_gateway_requests_total counter",
        f"atc_gateway_requests_total {stats.get('total_requests', 0)}",
        "# HELP atc_gateway_errors_total Total errors",
        f"atc_gateway_errors_total {stats.get('total_errors', 0)}",
    ]
    return "\n".join(lines), 200, {"Content-Type": "text/plain"}

# ── Entry Point ────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("GATEWAY_PORT", 4000))
    logger.info(f"[Gateway] Listening on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
