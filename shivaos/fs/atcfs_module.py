"""
ATCFS — ShivaOS Kernel Integration · Issue #23
Verbindet ATCFS mit dem ShivaOS Kernel (L2 Microkernel).
Stellt syscall-ähnliche FS-Operationen bereit.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.atcfs import ATCFileSystem, ATCFSNode
from typing import Optional

class ATCFSKernelModule:
    """
    Kernel-Modul: ATCFS ↔ ShivaOS Bridge.
    Registriert sich im ShivaOS als /dev/atcfs.
    """
    MODULE_NAME    = "atcfs"
    MODULE_VERSION = "1.0.0"
    DEVICE_PATH    = "/dev/atcfs"

    def __init__(self, owner: str = "kernel"):
        self.fs     = ATCFileSystem(owner=owner)
        self.owner  = owner
        self._loaded = False

    def load(self) -> bool:
        """Modul in Kernel laden."""
        try:
            self.fs.mkdir("/dev/atcfs", self.owner)
            self.fs.write("/proc/atcfs/version",
                          f"{self.MODULE_VERSION}".encode(), self.owner)
            self._loaded = True
            return True
        except Exception as e:
            print(f"  ⚠️ ATCFS Kernel-Load Fehler: {e}")
            return False

    def unload(self) -> bool:
        self._loaded = False
        return True

    # ── Syscall-Interface ────────────────────────────────────────
    def syscall_open(self, path: str, caller: str) -> Optional[ATCFSNode]:
        if not self._loaded: raise RuntimeError("ATCFS nicht geladen")
        try:
            _, node = self.fs.read(path, caller)
            return node
        except FileNotFoundError:
            return None

    def syscall_write(self, path: str, data: bytes, caller: str) -> ATCFSNode:
        if not self._loaded: raise RuntimeError("ATCFS nicht geladen")
        return self.fs.write(path, data, caller)

    def syscall_mkdir(self, path: str, caller: str) -> ATCFSNode:
        if not self._loaded: raise RuntimeError("ATCFS nicht geladen")
        return self.fs.mkdir(path, caller)

    def syscall_ls(self, path: str) -> list:
        if not self._loaded: raise RuntimeError("ATCFS nicht geladen")
        nodes = self.fs.ls(path)
        return [{"name": n.name, "is_dir": n.is_dir, "size": n.size,
                 "owner": n.owner, "cid": n.content_cid} for n in nodes]

    def syscall_stat(self) -> dict:
        return self.fs.stat()

    def syscall_mount(self, mountpoint: str, cid: str, caller: str):
        return self.fs.mount(mountpoint, cid, caller)

    def syscall_anchor(self) -> dict:
        """FS-Zustand in Blockchain verankern (Manifest exportieren)."""
        return self.fs.export_manifest()

# Singleton für Kernel
_atcfs_module: Optional[ATCFSKernelModule] = None

def get_atcfs() -> ATCFSKernelModule:
    global _atcfs_module
    if _atcfs_module is None:
        _atcfs_module = ATCFSKernelModule()
        _atcfs_module.load()
    return _atcfs_module
