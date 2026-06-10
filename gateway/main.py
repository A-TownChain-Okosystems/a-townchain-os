"""
API Gateway — Issue #25 (Kap. 8)
Port :4000 — Alle Middlewares aktiviert.
"""
from flask import Flask, request, jsonify, g
import time, os, json, urllib.request

from gateway.middleware.auth import require_api_key, validate_jwt
from gateway.middleware.rate_limit import rate_limiter
from gateway.middleware.logger import log_request
from gateway.middleware.signature_verify import verify_signature
from gateway.router import GatewayRouter

app    = Flask(__name__)
router = GatewayRouter(backend_url=os.environ.get("ATC_BACKEND_URL", "http://localhost:5000"))

# ── Middleware-Stack ────────────────────────────────────────────────────
@app.before_request
def before():
    g.start = time.time()
    g.request_id = f"req-{int(time.time()*1000)}"

    # Rate-Limit prüfen
    limiter_result = rate_limiter.check(request.remote_addr)
    if not limiter_result["allowed"]:
        return jsonify({"error": "Rate limit exceeded", "retry_after": limiter_result["retry_after"]}), 429

@app.after_request
def after(response):
    duration = round((time.time() - g.start) * 1000, 2)
    response.headers["X-Request-ID"]    = g.request_id
    response.headers["X-Response-Time"] = f"{duration}ms"
    response.headers["X-ATC-Version"]   = "2.0.0"
    log_request(request, response, duration)
    return response

# ── Health & Stats ───────────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({
        "status": "ok", "version": "2.0.0",
        "block_height": router.last_block_height,
        "peer_count":   router.peer_count,
        "tps":          router.tps,
        "uptime_s":     round(time.time() - router.started_at),
    })

@app.route("/api/stats")
def stats():
    return jsonify(router.stats())

# ── Public API (kein Auth) ────────────────────────────────────────────────
@app.route("/api/v1/blocks")
def blocks():
    return router.forward(request)

@app.route("/api/v1/blocks/<path:rest>")
def block_detail(rest):
    return router.forward(request)

@app.route("/api/v1/tx/<hash>")
def tx(hash):
    return router.forward(request)

@app.route("/api/v1/address/<addr>")
def address(addr):
    return router.forward(request)

@app.route("/api/v1/search")
def search():
    return router.forward(request)

# ── Authenticated API ─────────────────────────────────────────────────────
@app.route("/api/v1/wallet/balance", methods=["GET"])
@require_api_key
def wallet_balance():
    return router.forward(request)

@app.route("/api/v1/wallet/send", methods=["POST"])
@require_api_key
@verify_signature
def wallet_send():
    return router.forward(request)

@app.route("/api/v1/contracts/<path:rest>", methods=["GET","POST"])
@require_api_key
def contracts(rest):
    return router.forward(request)

@app.route("/api/v1/agents/<path:rest>", methods=["GET","POST","PUT"])
@require_api_key
def agents(rest):
    return router.forward(request)

# ── Admin API (JWT) ───────────────────────────────────────────────────────
@app.route("/api/admin/<path:rest>", methods=["GET","POST","DELETE"])
@validate_jwt
def admin(rest):
    return router.forward(request)

# ── Catch-all Router ─────────────────────────────────────────────────────
@app.route("/api/<path:rest>", methods=["GET","POST","PUT","PATCH","DELETE"])
def catchall(rest):
    return router.forward(request)

if __name__ == "__main__":
    port = int(os.environ.get("ATC_GATEWAY_PORT", 4000))
    print(f"🚀 A-TownChain Gateway v2.0.0 — Port {port}")
    print(f"   Backend: {router.backend_url}")
    print(f"   Rate-Limit: 100 req/min per IP")
    print(f"   Auth: API-Key + JWT + Signature-Verify")
    app.run(host="0.0.0.0", port=port, debug=False)
