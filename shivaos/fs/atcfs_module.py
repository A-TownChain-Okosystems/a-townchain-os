# Copyright (c) 2026 Michael Wroblewski / ShivaCore / A-TownChain-Okosystems. All Rights Reserved.
"""
ATCFS-Kernel-Modul fuer ShivaOS (Issue #23) — bindet core.atcfs.ATCFileSystem
als Kernel-Syscall-Schicht ein (load/syscall_write/syscall_ls/syscall_stat).
"""
from core.atcfs import ATCFileSystem


class ATCFSKernelModule:
    """Kernel-Modul-Wrapper um ATCFileSystem mit Syscall-artiger API."""

    def __init__(self, name: str = "kernel"):
        self.name = name
        self.fs: ATCFileSystem = None
        self.loaded = False

    def load(self) -> bool:
        self.fs = ATCFileSystem(owner=self.name)
        self.loaded = True
        return True

    def syscall_write(self, path: str, data: bytes, actor: str):
        if not self.loaded:
            raise RuntimeError("ATCFS-Modul nicht geladen")
        return self.fs.write(path, data, actor)

    def syscall_read(self, path: str, actor: str):
        if not self.loaded:
            raise RuntimeError("ATCFS-Modul nicht geladen")
        return self.fs.read(path, actor)

    def syscall_ls(self, path: str):
        if not self.loaded:
            raise RuntimeError("ATCFS-Modul nicht geladen")
        return self.fs.ls(path)

    def syscall_stat(self) -> dict:
        if not self.loaded:
            raise RuntimeError("ATCFS-Modul nicht geladen")
        files = sum(1 for n in self.fs.nodes.values() if not n.is_dir)
        dirs = sum(1 for n in self.fs.nodes.values() if n.is_dir)
        return {"files": files, "dirs": dirs, "total": len(self.fs.nodes)}
