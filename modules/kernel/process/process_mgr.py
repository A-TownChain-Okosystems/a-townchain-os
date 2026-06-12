"""
KAI-OS Kernel — Process Manager
Manages all OS-level processes, scheduling, and lifecycle.
Issue: Sprint 2.4 | Wiki: Kap. 58
"""
import threading
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger("kernel.process")


class ProcessState(Enum):
    CREATED  = "created"
    RUNNING  = "running"
    SLEEPING = "sleeping"
    STOPPED  = "stopped"
    ZOMBIE   = "zombie"


@dataclass
class Process:
    pid: str
    name: str
    target: Callable
    args: tuple = field(default_factory=tuple)
    state: ProcessState = ProcessState.CREATED
    thread: Optional[threading.Thread] = None
    created_at: float = field(default_factory=time.time)
    exit_code: int = 0

    def __post_init__(self):
        self.thread = threading.Thread(
            target=self._run,
            name=f"proc-{self.name}-{self.pid[:8]}",
            daemon=True
        )

    def _run(self):
        try:
            self.state = ProcessState.RUNNING
            self.target(*self.args)
            self.state = ProcessState.STOPPED
        except Exception as e:
            logger.error(f"Process {self.name} ({self.pid[:8]}) crashed: {e}")
            self.state = ProcessState.ZOMBIE
            self.exit_code = 1


class ProcessManager:
    """KAI-OS Process Manager — spawn, monitor, kill OS processes."""

    def __init__(self):
        self._processes: Dict[str, Process] = {}
        self._lock = threading.Lock()
        self._monitor_thread: Optional[threading.Thread] = None
        self._running = False
        logger.info("ProcessManager initialized")

    def spawn(self, name: str, target: Callable, args: tuple = ()) -> str:
        """Spawn a new process. Returns PID."""
        pid = str(uuid.uuid4())
        proc = Process(pid=pid, name=name, target=target, args=args)
        with self._lock:
            self._processes[pid] = proc
        proc.thread.start()
        logger.info(f"Spawned process '{name}' PID={pid[:8]}")
        return pid

    def kill(self, pid: str) -> bool:
        """Stop a process by PID."""
        with self._lock:
            proc = self._processes.get(pid)
        if not proc:
            logger.warning(f"kill: PID {pid[:8]} not found")
            return False
        proc.state = ProcessState.STOPPED
        logger.info(f"Killed process '{proc.name}' PID={pid[:8]}")
        return True

    def list_processes(self) -> List[Dict]:
        """Return list of all processes and their states."""
        with self._lock:
            return [
                {
                    "pid": p.pid[:8],
                    "name": p.name,
                    "state": p.state.value,
                    "uptime": round(time.time() - p.created_at, 1),
                    "exit_code": p.exit_code,
                }
                for p in self._processes.values()
            ]

    def get(self, pid: str) -> Optional[Process]:
        with self._lock:
            return self._processes.get(pid)

    def start_monitor(self, interval: float = 5.0):
        """Start background health monitor."""
        self._running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop, args=(interval,), daemon=True
        )
        self._monitor_thread.start()
        logger.info("Process monitor started")

    def _monitor_loop(self, interval: float):
        while self._running:
            with self._lock:
                for pid, proc in list(self._processes.items()):
                    if proc.state == ProcessState.ZOMBIE:
                        logger.warning(f"Zombie process detected: {proc.name} ({pid[:8]})")
            time.sleep(interval)

    def stop_monitor(self):
        self._running = False

    def status(self) -> Dict:
        procs = self.list_processes()
        return {
            "total": len(procs),
            "running": sum(1 for p in procs if p["state"] == "running"),
            "stopped": sum(1 for p in procs if p["state"] == "stopped"),
            "zombie":  sum(1 for p in procs if p["state"] == "zombie"),
            "processes": procs,
        }


# Singleton
_manager = ProcessManager()

def get_process_manager() -> ProcessManager:
    return _manager
