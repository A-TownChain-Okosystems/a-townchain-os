"""
Gateway Router v2.0.0 — Request-Forwarding + Circuit-Breaker
"""
import requests, time, logging
from flask import Response, jsonify

logger = logging.getLogger("atc.gateway.router")

class GatewayRouter:
    SERVICES = {
        "status":       "/api/status",
        "blockchain":   "/api/blockchain",
        "wallet":       "/api/wallet",
        "game":         "/api/game",
        "nodes":        "/api/nodes",
        "ai":           "/api/ai",
        "governance":   "/api/governance",
        "marketplace":  "/api/marketplace",
        "orchestrator": "/api/orchestrator",
    }

    def __init__(self, backend_url: str = "http://localhost:5000"):
        self.backend_url     = backend_url.rstrip("/")
        self._total_requests = 0
        self._total_errors   = 0
        self._circuit_open   = False
        self._circuit_errors = 0
        self._circuit_reset  = 0

    def _check_circuit(self) -> bool:
        if self._circuit_open:
            if time.time() > self._circuit_reset:
                self._circuit_open   = False
                self._circuit_errors = 0
                logger.info("[Router] Circuit Breaker CLOSED")
            else:
                return False
        return True

    def forward(self, request, path: str) -> Response:
        self._total_requests += 1
        if not self._check_circuit():
            return jsonify({"error": "Service temporarily unavailable", "code": 503}), 503

        target = f"{self.backend_url}/api/{path}"
        try:
            resp = requests.request(
                method  = request.method,
                url     = target,
                headers = {k: v for k,v in request.headers if k != "Host"},
                data    = request.get_data(),
                params  = request.args,
                timeout = 30,
                allow_redirects = False,
            )
            self._circuit_errors = max(0, self._circuit_errors - 1)
            return Response(
                resp.content,
                status       = resp.status_code,
                headers      = dict(resp.headers),
                content_type = resp.headers.get("Content-Type", "application/json"),
            )
        except requests.exceptions.ConnectionError:
            self._total_errors   += 1
            self._circuit_errors += 1
            if self._circuit_errors >= 5:
                self._circuit_open  = True
                self._circuit_reset = time.time() + 30
                logger.error("[Router] Circuit Breaker OPEN — Backend nicht erreichbar")
            return jsonify({"error": "Backend not reachable", "code": 503}), 503
        except requests.exceptions.Timeout:
            self._total_errors += 1
            return jsonify({"error": "Backend timeout", "code": 504}), 504
        except Exception as e:
            self._total_errors += 1
            logger.error(f"[Router] Unbekannter Fehler: {e}")
            return jsonify({"error": "Internal gateway error", "code": 500}), 500

    def check_backend(self) -> dict:
        try:
            r = requests.get(f"{self.backend_url}/api/status", timeout=3)
            return {"backend": "ok" if r.status_code == 200 else "degraded"}
        except:
            return {"backend": "offline"}

    def stats(self) -> dict:
        return {
            "total_requests": self._total_requests,
            "total_errors":   self._total_errors,
            "circuit_open":   self._circuit_open,
        }
