"""
API Orchestrator — ATS-1000 Standard
Zentraler Koordinator: Gateway → Orchestrator → Services.
Task-Routing, Load-Balancing, Circuit-Breaker, Event-Bus.
"""
import threading, time, logging, uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import auto, IntEnum
from collections import deque

logger = logging.getLogger("atc.orchestrator")

# ── Task-Typen ────────────────────────────────────────────
class TaskType(IntEnum):
    BLOCKCHAIN  = auto()
    WALLET      = auto()
    AI          = auto()
    GAME        = auto()
    GOVERNANCE  = auto()
    MARKETPLACE = auto()
    NODES       = auto()
    SYSTEM      = auto()

class TaskStatus(IntEnum):
    PENDING    = auto()
    RUNNING    = auto()
    DONE       = auto()
    FAILED     = auto()
    TIMEOUT    = auto()

@dataclass
class Task:
    id:        str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    type:      TaskType = TaskType.SYSTEM
    payload:   dict = field(default_factory=dict)
    status:    TaskStatus = TaskStatus.PENDING
    result:    Any = None
    error:     Optional[str] = None
    created:   float = field(default_factory=time.time)
    started:   Optional[float] = None
    finished:  Optional[float] = None
    timeout:   float = 30.0

    def duration(self) -> Optional[float]:
        if self.started and self.finished:
            return self.finished - self.started
        return None

# ── Service-Registry ──────────────────────────────────────
@dataclass
class ServiceEndpoint:
    name:       str
    handler:    Callable
    task_types: List[TaskType]
    max_rps:    int = 100
    _req_count: int = field(default=0, repr=False)
    _last_reset: float = field(default_factory=time.time, repr=False)
    _errors:    int = field(default=0, repr=False)
    _circuit_open: bool = field(default=False, repr=False)

    def is_available(self) -> bool:
        # Circuit-Breaker: nach 5 Fehlern öffnen
        if self._circuit_open:
            return False
        now = time.time()
        if now - self._last_reset > 1.0:
            self._req_count = 0
            self._last_reset = now
        return self._req_count < self.max_rps

    def call(self, payload: dict) -> Any:
        self._req_count += 1
        try:
            result = self.handler(payload)
            self._errors = max(0, self._errors - 1)
            return result
        except Exception as e:
            self._errors += 1
            if self._errors >= 5:
                self._circuit_open = True
                logger.error(f"[Orchestrator] Circuit breaker OPEN: {self.name}")
            raise

class APIOrchestrator:
    """
    Zentraler Service-Router mit:
    - Round-Robin Load-Balancing
    - Circuit-Breaker pro Service
    - Async Task-Queue
    - Event-Bus Integration
    - Health-Monitoring
    """

    def __init__(self):
        self._services:  Dict[TaskType, List[ServiceEndpoint]] = {}
        self._task_queue: deque = deque(maxlen=1000)
        self._tasks:     Dict[str, Task] = {}
        self._rr_idx:    Dict[TaskType, int] = {}
        self._lock       = threading.Lock()
        self._running    = False
        self._worker_threads: List[threading.Thread] = []
        self._event_hooks: Dict[str, List[Callable]] = {}
        self._stats = {"total": 0, "success": 0, "failed": 0, "timeout": 0}

    # ── Service registrieren ──────────────────────────────
    def register(self, service: ServiceEndpoint):
        for tt in service.task_types:
            self._services.setdefault(tt, []).append(service)
        logger.info(f"[Orchestrator] Service registriert: {service.name}")

    def register_fn(self, name: str, handler: Callable,
                    task_types: List[TaskType], max_rps: int = 100):
        self.register(ServiceEndpoint(name, handler, task_types, max_rps))

    # ── Task dispatchen ───────────────────────────────────
    def dispatch(self, task_type: TaskType, payload: dict,
                 timeout: float = 30.0) -> Task:
        task = Task(type=task_type, payload=payload, timeout=timeout)
        with self._lock:
            self._tasks[task.id] = task
            self._task_queue.append(task.id)
            self._stats["total"] += 1
        return task

    def dispatch_sync(self, task_type: TaskType, payload: dict,
                      timeout: float = 30.0) -> Any:
        """Synchroner Dispatch — wartet auf Ergebnis."""
        task = self.dispatch(task_type, payload, timeout)
        deadline = time.time() + timeout
        while task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            if time.time() > deadline:
                task.status = TaskStatus.TIMEOUT
                self._stats["timeout"] += 1
                raise TimeoutError(f"Task {task.id} timed out")
            time.sleep(0.01)
        if task.status == TaskStatus.FAILED:
            raise RuntimeError(task.error or "Task failed")
        return task.result

    # ── Worker ────────────────────────────────────────────
    def _worker(self):
        while self._running:
            task_id = None
            with self._lock:
                if self._task_queue:
                    task_id = self._task_queue.popleft()
            if not task_id:
                time.sleep(0.005)
                continue
            task = self._tasks.get(task_id)
            if not task:
                continue
            self._execute(task)

    def _execute(self, task: Task):
        services = self._services.get(task.type, [])
        available = [s for s in services if s.is_available()]
        if not available:
            task.status = TaskStatus.FAILED
            task.error  = f"No service for {task.type.name}"
            self._stats["failed"] += 1
            return

        # Round-Robin
        idx = self._rr_idx.get(task.type, 0) % len(available)
        self._rr_idx[task.type] = (idx + 1) % len(available)
        svc = available[idx]

        task.status  = TaskStatus.RUNNING
        task.started = time.time()
        try:
            task.result   = svc.call(task.payload)
            task.status   = TaskStatus.DONE
            task.finished = time.time()
            self._stats["success"] += 1
            self._emit(f"task.done.{task.type.name.lower()}", task)
        except Exception as e:
            task.status   = TaskStatus.FAILED
            task.error    = str(e)
            task.finished = time.time()
            self._stats["failed"] += 1
            logger.error(f"[Orchestrator] Task {task.id} failed: {e}")

    # ── Event-Bus ─────────────────────────────────────────
    def on(self, event: str, fn: Callable):
        self._event_hooks.setdefault(event, []).append(fn)

    def _emit(self, event: str, data: Any):
        for fn in self._event_hooks.get(event, []):
            try: fn(data)
            except: pass

    # ── Start/Stop ────────────────────────────────────────
    def start(self, workers: int = 4):
        self._running = True
        for _ in range(workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self._worker_threads.append(t)
        logger.info(f"[Orchestrator] Gestartet ({workers} Worker)")

    def stop(self):
        self._running = False
        logger.info("[Orchestrator] Gestoppt")

    # ── Health / Stats ────────────────────────────────────
    def health(self) -> dict:
        services_health = {}
        for tt, svcs in self._services.items():
            services_health[tt.name] = [
                {"name": s.name, "available": s.is_available(),
                 "circuit_open": s._circuit_open}
                for s in svcs
            ]
        return {
            "status":   "ok" if self._running else "stopped",
            "stats":    self._stats,
            "queue":    len(self._task_queue),
            "services": services_health,
        }
