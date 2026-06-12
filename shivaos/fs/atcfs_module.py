"""
ATCFS — ShivaOS Kernel Integration (v3.2.1)
Nutzt jetzt kanonische Implementierung aus modules.kernel.atcfs
Wiki: Kap. 45
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from modules.kernel.atcfs.atcfs import ATCFileSystem, ATCFSNode, ATCFS, get_vfs, get_atcfs
from typing import Optional


class ATCFSKernelModule:
    """
    ShivaOS Kernel-Modul: ATCFS Bridge.
    Registriert sich im ShivaOS als /dev/atcfs.
    """
    MODULE_NAME    = "atcfs"
    MODULE_VERSION = "2.0.0"
    DEVICE_PATH    = "/dev/atcfs"

    def __init__(self, owner: str = "kernel"):
        self.vfs    = get_vfs(owner=owner)
        self.store  = get_atcfs()
        self.owner  = owner
        self._loaded = False

    def load(self) -> bool:
        try:
            self.vfs.mkdir("/dev", self.owner)
            self.vfs.mkdir(self.DEVICE_PATH, self.owner)
            self._loaded = True
            return True
        except Exception:
            return False

    def unload(self) -> bool:
        self._loaded = False
        return True

    def syscall_write(self, path: str, data: bytes) -> str:
        """Kernel syscall: write → ATCFS VFS + Object-Store."""
        node = self.vfs.write(path, data, self.owner)
        cid  = self.store.write(path.split("/")[-1], data, tags=["kernel"])
        return cid

    def syscall_read(self, path: str) -> Optional[bytes]:
        """Kernel syscall: read → ATCFS Object-Store via CID."""
        cid, _ = self.vfs.read(path, self.owner)
        return self.store.read(cid)

    def syscall_ls(self, path: str):
        return self.vfs.ls(path)

    def status(self) -> dict:
        return {
            "module": self.MODULE_NAME,
            "version": self.MODULE_VERSION,
            "loaded": self._loaded,
            "vfs": self.vfs.stat(),
            "store": self.store.stats(),
        }


# Singleton
_module: Optional[ATCFSKernelModule] = None

def get_atcfs_module(owner: str = "kernel") -> ATCFSKernelModule:
    global _module
    if _module is None:
        _module = ATCFSKernelModule(owner=owner)
        _module.load()
    return _module
