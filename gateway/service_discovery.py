"""
ATC Gateway — Service Discovery
Manages dynamic registration and health-check of backend services.
Wiki: Kap. 8
"""
import time
import threading
import logging
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("gateway.discovery")

HEALTH_INTERVAL = 10.0   # seconds between health checks
SERVICE_TIMEOUT  = 5.0   # HTTP timeout for health checks


@dataclass
class ServiceEndpoint:
    name: str
    host: str
    port: int
    health_path: str = "/health"
    healthy: bool = False
    last_check: float = field(default_factory=time.time)
    response_ms: float = 0.0
    version: str = "unknown"
    metadata: Dict = field(default_factory=dict)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}{self.health_path}"


# Default A-TownChain OS services
DEFAULT_SERVICES = [
    ServiceEndpoint("gateway",    "127.0.0.1", 4000, "/health"),
    ServiceEndpoint("core",       "127.0.0.1", 5000, "/health"),
    ServiceEndpoint("chain",      "127.0.0.1", 5001, "/health"),
    ServiceEndpoint("wallet",     "127.0.0.1", 5002, "/health"),
    ServiceEndpoint("ai",         "127.0.0.1", 5003, "/health"),
    ServiceEndpoint("game",       "127.0.0.1", 5004, "/health"),
    ServiceEndpoint("prometheus", "127.0.0.1", 9100, "/health"),
]


class ServiceDiscovery:
    """
    Dynamic service registry with health-check and auto-failover.
    Services register themselves and are periodically polled.
    """

    def __init__(self, services: List[ServiceEndpoint] = None):
        self._services: Dict[str, ServiceEndpoint] = {}
        self._lock = threading.Lock()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None

        for svc in (services or DEFAULT_SERVICES):
            self.register(svc)

    def register(self, svc: ServiceEndpoint):
        """Register a new service."""
        with self._lock:
            self._services[svc.name] = svc
        logger.info(f"Service registered: {svc.name} @ {svc.base_url}")

    def deregister(self, name: str) -> bool:
        """Remove a service from the registry."""
        with self._lock:
            if name in self._services:
                del self._services[name]
                logger.info(f"Service deregistered: {name}")
                return True
        return False

    def get(self, name: str) -> Optional[ServiceEndpoint]:
        """Get a healthy service endpoint."""
        with self._lock:
            svc = self._services.get(name)
        if svc and svc.healthy:
            return svc
        return None

    def get_url(self, name: str, path: str = "") -> Optional[str]:
        """Get full URL for a service path, or None if unhealthy."""
        svc = self.get(name)
        return f"{svc.base_url}{path}" if svc else None

    def list_services(self) -> List[Dict]:
        with self._lock:
            return [
                {
                    "name": s.name,
                    "url": s.base_url,
                    "healthy": s.healthy,
                    "response_ms": round(s.response_ms, 1),
                    "version": s.version,
                    "last_check": time.strftime("%H:%M:%S", time.localtime(s.last_check)),
                }
                for s in self._services.values()
            ]

    def healthy_services(self) -> List[str]:
        with self._lock:
            return [name for name, s in self._services.items() if s.healthy]

    def start_health_monitor(self):
        """Start background health-check loop."""
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._health_loop, daemon=True
        )
        self._monitor_thread.start()
        logger.info("Service health monitor started")

    def stop_health_monitor(self):
        self._running = False

    def _health_loop(self):
        while self._running:
            with self._lock:
                services = list(self._services.values())
            for svc in services:
                self._check(svc)
            time.sleep(HEALTH_INTERVAL)

    def _check(self, svc: ServiceEndpoint):
        start = time.time()
        try:
            r = requests.get(svc.health_url, timeout=SERVICE_TIMEOUT)
            elapsed = (time.time() - start) * 1000
            was_healthy = svc.healthy
            svc.healthy = r.status_code == 200
            svc.response_ms = elapsed
            svc.last_check = time.time()
            if "version" in r.headers:
                svc.version = r.headers["version"]
            if not was_healthy and svc.healthy:
                logger.info(f"Service {svc.name} recovered ({elapsed:.0f}ms)")
            elif was_healthy and not svc.healthy:
                logger.warning(f"Service {svc.name} went unhealthy ({r.status_code})")
        except Exception as e:
            svc.healthy = False
            svc.response_ms = (time.time() - start) * 1000
            svc.last_check = time.time()
            logger.debug(f"Health check failed {svc.name}: {e}")

    def force_check_all(self):
        """Run health checks immediately (blocking)."""
        with self._lock:
            services = list(self._services.values())
        for svc in services:
            self._check(svc)

    def status(self) -> Dict:
        svcs = self.list_services()
        healthy = sum(1 for s in svcs if s["healthy"])
        return {
            "total": len(svcs),
            "healthy": healthy,
            "unhealthy": len(svcs) - healthy,
            "services": svcs,
        }


_discovery = ServiceDiscovery()

def get_discovery() -> ServiceDiscovery:
    return _discovery
