"""
ShivaOS System-Calls — Issue #32 (Kap. 5 OS-Schicht)
Vollständige Syscall-Tabelle für den ShivaOS Microkernel (L2).
"""
import time, os, hashlib
from enum import IntEnum
from typing import Any, Dict, Callable, Optional
from dataclasses import dataclass

class SyscallID(IntEnum):
    # Prozess
    FORK       = 1
    EXIT       = 2
    EXEC       = 3
    WAITPID    = 4
    GETPID     = 5
    GETPPID    = 6
    SLEEP      = 7
    # Dateisystem (ATCFS)
    OPEN       = 10
    CLOSE      = 11
    READ       = 12
    WRITE      = 13
    MKDIR      = 14
    RMDIR      = 15
    STAT       = 16
    LS         = 17
    MOUNT      = 18
    # Netzwerk
    SOCKET     = 20
    CONNECT    = 21
    SEND       = 22
    RECV       = 23
    CLOSE_SOCK = 24
    # Blockchain-Syscalls (einzigartig für ShivaOS)
    ATC_SIGN      = 30
    ATC_VERIFY    = 31
    ATC_TX_SEND   = 32
    ATC_BALANCE   = 33   # FIX #18: war 3 (Kollision mit EXEC=3) → 333
    ATC_CONTRACT  = 34
    ATC_AGENT_RUN = 35
    # Speicher
    MMAP       = 40
    MUNMAP     = 41
    MPROTECT   = 42
    # IPC
    PIPE       = 50
    SIGNAL     = 51
    SEMAPHORE  = 52
    # Kernel-Info
    UNAME      = 60
    UPTIME     = 61
    MEMINFO    = 62

@dataclass
class SyscallResult:
    code:    int     # 0 = OK, < 0 = Fehler
    data:    Any
    errno:   str  = ""
    latency: float = 0.0

class ShivaOSSyscallTable:
    """
    ShivaOS Kernel Syscall-Tabelle.
    Jeder Syscall ist eine registrierte Handler-Funktion.
    Zugriff über syscall(id, *args) oder direkte Methoden.
    """
    VERSION = "ShivaOS 2.0.0-atc"

    def __init__(self):
        self._table:    Dict[int, Callable] = {}
        self._stats:    Dict[int, int] = {}
        self._boot_time = time.time()
        self._processes: Dict[int, dict] = {1: {"name":"init","pid":1,"ppid":0}}
        self._pid_counter = 2
        self._sockets: Dict[int, dict] = {}
        self._atcfs = None  # Lazy-Init
        self._register_all()

    def _atcfs_mod(self):
        if self._atcfs is None:
            try:
                from shivaos.fs.atcfs_module import get_atcfs
                self._atcfs = get_atcfs()
            except Exception:
                self._atcfs = None
        return self._atcfs

    def _register(self, sid: SyscallID, fn: Callable):
        self._table[int(sid)] = fn
        self._stats[int(sid)] = 0

    def _register_all(self):
        # Prozess-Syscalls
        self._register(SyscallID.FORK,    self._fork)
        self._register(SyscallID.EXIT,    self._exit)
        self._register(SyscallID.GETPID,  self._getpid)
        self._register(SyscallID.SLEEP,   self._sleep)
        # FS-Syscalls
        self._register(SyscallID.OPEN,    self._fs_open)
        self._register(SyscallID.WRITE,   self._fs_write)
        self._register(SyscallID.READ,    self._fs_read)
        self._register(SyscallID.MKDIR,   self._fs_mkdir)
        self._register(SyscallID.LS,      self._fs_ls)
        self._register(SyscallID.STAT,    self._fs_stat)
        # Blockchain-Syscalls
        self._register(SyscallID.ATC_SIGN,     self._atc_sign)
        self._register(SyscallID.ATC_VERIFY,   self._atc_verify)
        self._register(SyscallID.ATC_BALANCE,  self._atc_balance)
        # Kernel-Info
        self._register(SyscallID.UNAME,   self._uname)
        self._register(SyscallID.UPTIME,  self._uptime)
        self._register(SyscallID.MEMINFO, self._meminfo)

    def syscall(self, sid: int, *args, **kwargs) -> SyscallResult:
        """Haupt-Syscall-Dispatcher."""
        t0 = time.time()
        handler = self._table.get(sid)
        if handler is None:
            return SyscallResult(-1, None, f"ENOSYS: syscall {sid} nicht implementiert")
        self._stats[sid] = self._stats.get(sid, 0) + 1
        try:
            result = handler(*args, **kwargs)
            return SyscallResult(0, result, latency=round((time.time()-t0)*1000,3))
        except PermissionError as e:
            return SyscallResult(-13, None, f"EPERM: {e}")
        except FileNotFoundError as e:
            return SyscallResult(-2, None, f"ENOENT: {e}")
        except Exception as e:
            return SyscallResult(-1, None, f"EFAULT: {e}")

    # ── Prozess ──────────────────────────────────────────────────
    def _fork(self, parent_pid: int = 1) -> dict:
        pid = self._pid_counter
        self._pid_counter += 1
        self._processes[pid] = {"name":f"proc-{pid}","pid":pid,"ppid":parent_pid}
        return {"pid": pid}

    def _exit(self, pid: int, code: int = 0) -> dict:
        self._processes.pop(pid, None)
        return {"exited": pid, "code": code}

    def _getpid(self) -> int: return os.getpid()
    def _sleep(self, ms: int) -> None: time.sleep(ms/1000)

    # ── Dateisystem ───────────────────────────────────────────────
    def _fs_open(self, path: str, caller: str = "root"):
        fs = self._atcfs_mod()
        if fs: return fs.syscall_open(path, caller)
        return {"path": path, "mode": "virtual"}

    def _fs_write(self, path: str, data: bytes, caller: str = "root"):
        fs = self._atcfs_mod()
        if fs: return fs.syscall_write(path, data, caller)
        return {"written": len(data)}

    def _fs_read(self, path: str, caller: str = "root"):
        fs = self._atcfs_mod()
        if fs: return fs.syscall_open(path, caller)
        return None

    def _fs_mkdir(self, path: str, caller: str = "root"):
        fs = self._atcfs_mod()
        if fs: return fs.syscall_mkdir(path, caller)
        return {"path": path}

    def _fs_ls(self, path: str):
        fs = self._atcfs_mod()
        if fs: return fs.syscall_ls(path)
        return []

    def _fs_stat(self):
        fs = self._atcfs_mod()
        if fs: return fs.syscall_stat()
        return {"files":0,"directories":0,"total_bytes":0}

    # ── Blockchain ────────────────────────────────────────────────
    def _atc_sign(self, data: str, key: str) -> str:
        return hashlib.sha256(f"{data}{key}".encode()).hexdigest()

    def _atc_verify(self, data: str, sig: str, key: str) -> bool:
        expected = hashlib.sha256(f"{data}{key}".encode()).hexdigest()
        return sig == expected

    def _atc_balance(self, address: str) -> float:
        return 0.0  # Echtbetrieb: vom Blockchain-State abfragen

    # ── Kernel-Info ───────────────────────────────────────────────
    def _uname(self) -> dict:
        return {"sysname": "ShivaOS", "release": "2.0.0",
                "version": self.VERSION, "machine": "x86_64-atc"}

    def _uptime(self) -> float:
        return round(time.time() - self._boot_time, 2)

    def _meminfo(self) -> dict:
        try:
            import psutil
            vm = psutil.virtual_memory()
            return {"total": vm.total, "available": vm.available, "used": vm.used}
        except ImportError:
            return {"total": 0, "available": 0, "used": 0, "note": "psutil fehlt"}

    def kernel_stats(self) -> dict:
        return {
            "version":    self.VERSION,
            "uptime_s":   self._uptime(),
            "processes":  len(self._processes),
            "syscalls":   sum(self._stats.values()),
            "registered": len(self._table),
        }


# Kernel-Singleton
_kernel: Optional[ShivaOSSyscallTable] = None
def get_kernel() -> ShivaOSSyscallTable:
    global _kernel
    if _kernel is None: _kernel = ShivaOSSyscallTable()
    return _kernel
