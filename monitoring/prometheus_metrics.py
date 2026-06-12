"""
A-TownChain OS — Prometheus Metrics Exporter
Exposes /metrics endpoint for Grafana dashboards.
Issue: #44 | Wiki: Kap. 49
"""
import time
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, List
from dataclasses import dataclass, field

logger = logging.getLogger("monitoring.prometheus")

METRICS_PORT = 9100


@dataclass
class Gauge:
    name: str
    help: str
    value: float = 0.0
    labels: Dict[str, str] = field(default_factory=dict)

    def set(self, value: float, labels: Dict[str, str] = None):
        self.value = value
        if labels:
            self.labels = labels


@dataclass
class Counter:
    name: str
    help: str
    value: float = 0.0

    def inc(self, amount: float = 1.0):
        self.value += amount


class MetricsRegistry:
    """Prometheus-compatible metrics registry."""

    def __init__(self):
        self._gauges: Dict[str, Gauge] = {}
        self._counters: Dict[str, Counter] = {}
        self._lock = threading.Lock()
        self._register_defaults()

    def _register_defaults(self):
        self.gauge("atc_block_height",         "Current block height")
        self.gauge("atc_block_time_seconds",   "Time between last two blocks")
        self.gauge("atc_mempool_size",         "Number of transactions in mempool")
        self.gauge("atc_peer_count",           "Number of connected peers")
        self.gauge("atc_tps",                  "Transactions per second")
        self.gauge("atc_validator_count",      "Number of active validators")
        self.gauge("atc_chain_id",             "Chain ID")
        self.gauge("atc_total_supply",         "Total ATC supply in atoshi")
        self.counter("atc_tx_total",           "Total transactions processed")
        self.counter("atc_block_total",        "Total blocks produced")
        self.counter("atc_ipc_messages_total", "Total IPC bus messages")
        self.counter("atc_api_requests_total", "Total API Gateway requests")
        self.counter("atc_ai_queries_total",   "Total AI kernel queries")

    def gauge(self, name: str, help_text: str) -> Gauge:
        with self._lock:
            if name not in self._gauges:
                self._gauges[name] = Gauge(name=name, help=help_text)
            return self._gauges[name]

    def counter(self, name: str, help_text: str) -> Counter:
        with self._lock:
            if name not in self._counters:
                self._counters[name] = Counter(name=name, help=help_text)
            return self._counters[name]

    def set(self, name: str, value: float):
        with self._lock:
            if name in self._gauges:
                self._gauges[name].set(value)

    def inc(self, name: str, amount: float = 1.0):
        with self._lock:
            if name in self._counters:
                self._counters[name].inc(amount)

    def render(self) -> str:
        """Render metrics in Prometheus text format."""
        lines = []
        with self._lock:
            for name, g in self._gauges.items():
                lines.append(f"# HELP {name} {g.help}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {g.value}")
            for name, c in self._counters.items():
                lines.append(f"# HELP {name} {c.help}")
                lines.append(f"# TYPE {name} counter")
                lines.append(f"{name} {c.value}")
        return "\n".join(lines) + "\n"


_registry = MetricsRegistry()


class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            body = _registry.render().encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # suppress default HTTP logging


def start_metrics_server(port: int = METRICS_PORT):
    """Start Prometheus metrics HTTP server in background thread."""
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Prometheus metrics server started on :{port}/metrics")
    return server


def get_registry() -> MetricsRegistry:
    return _registry
