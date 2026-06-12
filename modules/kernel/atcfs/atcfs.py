"""
ATCFS — A-TownChain Filesystem  (Kanonische Implementierung)
Vereint: modules/kernel/atcfs/ + core/atcfs  →  v3.2.1

Bietet zwei Ebenen:
  1. ATCFileSystem  — POSIX-ähnliches VFS mit Permissions, Verzeichnisbaum,
                      Encryption-Flag, Merkle-Hash, mount(), export_manifest()
  2. ATCFS          — Content-adressiertes Object-Store (CID/SHA256, pin, gc)

Standards: ATS-1001 Storage Layer
Wiki: Kap. 45, Kap. 58
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("kernel.atcfs")

# ─── Konfiguration ────────────────────────────────────────────────────────────
ATCFS_ROOT = os.path.join(os.path.expanduser("~"), ".atcfs")


# ══════════════════════════════════════════════════════════════════════════════
# EBENE 1: POSIX-ähnliches Virtual Filesystem (ehemals core/atcfs.py)
# ══════════════════════════════════════════════════════════════════════════════

class FilePermission(Enum):
    READ    = "r"
    WRITE   = "w"
    EXECUTE = "x"
    OWNER   = "o"


@dataclass
class ATCFSNode:
    """Einzelner Knoten im Dateisystem-Baum."""
    name:        str
    path:        str
    is_dir:      bool
    owner:       str
    size:        int  = 0
    content_cid: str  = ""
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    created:     float = field(default_factory=time.time)
    modified:    float = field(default_factory=time.time)
    children:    List[str] = field(default_factory=list)
    encrypted:   bool  = False
    merkle_hash: str   = ""
    pinned:      bool  = False
    tags:        List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.merkle_hash:
            self.merkle_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = f"{self.name}{self.owner}{self.size}{self.content_cid}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]


class ATCFileSystem:
    """
    A-TownChain Virtual Filesystem (VFS).
    POSIX-ähnlich: Verzeichnisse, Permissions, Mounting, Merkle-Manifest.
    Standard: ATS-1001 | Wiki: Kap. 45
    """
    ROOT = "/"

    def __init__(self, owner: str = "system"):
        self._nodes: Dict[str, ATCFSNode] = {}
        self._owner  = owner
        self._lock   = threading.Lock()
        self._init_root()

    # ── Init ──────────────────────────────────────────────────────
    def _init_root(self):
        root = ATCFSNode(
            name="/", path="/", is_dir=True, owner=self._owner,
            permissions={"system": ["r","w","x","o"], "world": ["r","x"]},
        )
        self._nodes["/"] = root
        for d in ["/home", "/tmp", "/var", "/var/log", "/var/data",
                  "/proc", "/sys", "/dev", "/mnt",
                  "/atc", "/atc/contracts", "/atc/wallets",
                  "/atc/chain", "/atc/peers"]:
            self.mkdir(d, self._owner)

    # ── Pfad-Helpers ──────────────────────────────────────────────
    def _resolve(self, path: str) -> str:
        parts = [p for p in path.split("/") if p]
        return "/" + "/".join(parts) if parts else "/"

    def _parent(self, path: str) -> str:
        r = self._resolve(path)
        parts = r.rstrip("/").rsplit("/", 1)
        return parts[0] if parts[0] else "/"

    # ── CRUD ──────────────────────────────────────────────────────
    def exists(self, path: str) -> bool:
        return self._resolve(path) in self._nodes

    def mkdir(self, path: str, owner: str, parents: bool = True) -> ATCFSNode:
        r = self._resolve(path)
        if r in self._nodes:
            return self._nodes[r]
        parent = self._parent(r)
        if parents and parent != r and parent not in self._nodes:
            self.mkdir(parent, owner, parents=True)
        node = ATCFSNode(
            name=r.rsplit("/", 1)[-1] or "/", path=r, is_dir=True, owner=owner,
            permissions={owner: ["r","w","x","o"]},
        )
        with self._lock:
            self._nodes[r] = node
            if parent in self._nodes and r not in self._nodes[parent].children:
                self._nodes[parent].children.append(r)
        return node

    def write(self, path: str, content: bytes, owner: str,
              encrypt: bool = False, tags: List[str] = None) -> ATCFSNode:
        r = self._resolve(path)
        parent = self._parent(r)
        if parent not in self._nodes:
            self.mkdir(parent, owner, parents=True)
        cid = "atcfs://" + hashlib.sha256(content).hexdigest()
        node = ATCFSNode(
            name=r.rsplit("/", 1)[-1], path=r, is_dir=False,
            owner=owner, size=len(content), content_cid=cid,
            encrypted=encrypt, modified=time.time(),
            permissions={owner: ["r","w","o"]},
            tags=tags or [],
        )
        with self._lock:
            self._nodes[r] = node
            if r not in self._nodes.get(parent, ATCFSNode("","",False,"")).children:
                if parent in self._nodes:
                    self._nodes[parent].children.append(r)
        return node

    def read(self, path: str, requester: str) -> Tuple[str, ATCFSNode]:
        """CID zurückgeben (Inhalt liegt im ATCFS Object-Store)."""
        r = self._resolve(path)
        if r not in self._nodes:
            raise FileNotFoundError(f"Pfad nicht gefunden: {r}")
        node = self._nodes[r]
        perms = node.permissions.get(requester, node.permissions.get("world", []))
        if "r" not in perms and node.owner != requester:
            raise PermissionError(f"{requester} darf {r} nicht lesen")
        return node.content_cid, node

    def ls(self, path: str) -> List[ATCFSNode]:
        r = self._resolve(path)
        if r not in self._nodes:
            raise FileNotFoundError(r)
        node = self._nodes[r]
        if not node.is_dir:
            return [node]
        return [self._nodes[c] for c in node.children if c in self._nodes]

    def rm(self, path: str, owner: str, recursive: bool = False) -> bool:
        r = self._resolve(path)
        if r not in self._nodes:
            return False
        node = self._nodes[r]
        if node.owner != owner:
            raise PermissionError("Nur Owner darf löschen")
        if node.is_dir and node.children and not recursive:
            raise IsADirectoryError("Verzeichnis nicht leer — benutze recursive=True")
        if recursive:
            for child in list(node.children):
                self.rm(child, owner, recursive=True)
        parent = self._parent(r)
        with self._lock:
            if parent in self._nodes:
                self._nodes[parent].children = [
                    c for c in self._nodes[parent].children if c != r
                ]
            del self._nodes[r]
        return True

    def pin(self, path: str) -> bool:
        r = self._resolve(path)
        if r in self._nodes:
            self._nodes[r].pinned = True
            return True
        return False

    def unpin(self, path: str) -> bool:
        r = self._resolve(path)
        if r in self._nodes:
            self._nodes[r].pinned = False
            return True
        return False

    def mount(self, mountpoint: str, remote_cid: str, owner: str) -> ATCFSNode:
        """Remote ATCFS-Volume (via CID) einbinden."""
        mp = self._resolve(mountpoint)
        self.mkdir(mp, owner)
        return self.write(f"{mp}/.atcfs_mount", remote_cid.encode(), owner)

    def export_manifest(self) -> dict:
        """FS-Baum als JSON-Manifest exportieren (für Blockchain-Anchoring)."""
        manifest = {}
        for path, node in self._nodes.items():
            manifest[path] = {
                "name": node.name, "is_dir": node.is_dir,
                "owner": node.owner, "size": node.size,
                "cid": node.content_cid, "hash": node.merkle_hash,
                "modified": node.modified, "pinned": node.pinned,
            }
        root_hash = hashlib.sha256(
            json.dumps(manifest, sort_keys=True).encode()
        ).hexdigest()
        return {"root_hash": root_hash, "entries": len(manifest), "fs": manifest}

    def stat(self) -> dict:
        dirs  = sum(1 for n in self._nodes.values() if n.is_dir)
        files = sum(1 for n in self._nodes.values() if not n.is_dir)
        total = sum(n.size for n in self._nodes.values())
        return {
            "total_nodes": len(self._nodes), "directories": dirs,
            "files": files, "total_bytes": total,
        }


# ══════════════════════════════════════════════════════════════════════════════
# EBENE 2: Content-adressierter Object-Store (ehemals modules/kernel/atcfs/)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ATCObject:
    """Ein gespeichertes Objekt im Content-adressierten Store."""
    cid: str
    name: str
    size: int
    content_hash: str
    created_at: float = field(default_factory=time.time)
    pinned: bool = False
    tags: List[str] = field(default_factory=list)


class ATCFS:
    """
    ATCFS Object-Store — content-addressed, persistent, thread-safe.
    Speichert beliebige Binärdaten unter SHA256-CIDs.
    Integriert mit ATCFileSystem für vollständige FS-Semantik.
    Wiki: Kap. 58
    """

    def __init__(self, root: str = ATCFS_ROOT):
        self.root = root
        self._index: Dict[str, ATCObject] = {}
        self._lock  = threading.Lock()
        os.makedirs(os.path.join(root, "objects"), exist_ok=True)
        os.makedirs(os.path.join(root, "meta"),    exist_ok=True)
        self._load_index()
        logger.info(f"ATCFS Object-Store: {root} ({len(self._index)} objects)")

    # ── CID ───────────────────────────────────────────────────────
    @staticmethod
    def compute_cid(data: bytes) -> str:
        return "atcfs://" + hashlib.sha256(data).hexdigest()

    def _obj_path(self, cid: str) -> str:
        h = cid.replace("atcfs://", "")
        return os.path.join(self.root, "objects", h[:2], h[2:])

    # ── CRUD ──────────────────────────────────────────────────────
    def write(self, name: str, data: bytes, tags: List[str] = None) -> str:
        cid = self.compute_cid(data)
        obj_path = self._obj_path(cid)
        os.makedirs(os.path.dirname(obj_path), exist_ok=True)
        if not os.path.exists(obj_path):
            with open(obj_path, "wb") as f:
                f.write(data)
        obj = ATCObject(
            cid=cid, name=name, size=len(data),
            content_hash=cid.replace("atcfs://", ""),
            tags=tags or [],
        )
        with self._lock:
            self._index[cid] = obj
        self._save_index()
        return cid

    def read(self, cid: str) -> Optional[bytes]:
        obj_path = self._obj_path(cid)
        if not os.path.exists(obj_path):
            return None
        with open(obj_path, "rb") as f:
            return f.read()

    def exists(self, cid: str) -> bool:
        return cid in self._index

    def delete(self, cid: str, force: bool = False) -> bool:
        with self._lock:
            obj = self._index.get(cid)
        if not obj:
            return False
        if obj.pinned and not force:
            logger.warning(f"Cannot delete pinned object {cid[:20]}")
            return False
        obj_path = self._obj_path(cid)
        if os.path.exists(obj_path):
            os.remove(obj_path)
        with self._lock:
            del self._index[cid]
        self._save_index()
        return True

    # ── Pin / GC ──────────────────────────────────────────────────
    def pin(self, cid: str) -> bool:
        with self._lock:
            if cid in self._index:
                self._index[cid].pinned = True
                self._save_index()
                return True
        return False

    def unpin(self, cid: str) -> bool:
        with self._lock:
            if cid in self._index:
                self._index[cid].pinned = False
                self._save_index()
                return True
        return False

    def gc(self) -> int:
        """Garbage-collect unpinned objects. Returns count of removed items."""
        removed = 0
        with self._lock:
            to_remove = [cid for cid, obj in self._index.items() if not obj.pinned]
        for cid in to_remove:
            if self.delete(cid, force=False):
                removed += 1
        logger.info(f"ATCFS GC: removed {removed} objects")
        return removed

    def list_objects(self, tag: str = None) -> List[Dict]:
        with self._lock:
            objs = list(self._index.values())
        if tag:
            objs = [o for o in objs if tag in o.tags]
        return [
            {"cid": o.cid, "name": o.name, "size": o.size,
             "pinned": o.pinned, "tags": o.tags,
             "created": time.strftime("%Y-%m-%d", time.localtime(o.created_at))}
            for o in objs
        ]

    def stats(self) -> Dict:
        with self._lock:
            objs = list(self._index.values())
        return {
            "total_objects": len(objs),
            "total_bytes":   sum(o.size for o in objs),
            "pinned":        sum(1 for o in objs if o.pinned),
            "root":          self.root,
        }

    # ── Persistenz ────────────────────────────────────────────────
    def _save_index(self):
        idx = {
            cid: {"cid": o.cid, "name": o.name, "size": o.size,
                  "content_hash": o.content_hash, "created_at": o.created_at,
                  "pinned": o.pinned, "tags": o.tags}
            for cid, o in self._index.items()
        }
        with open(os.path.join(self.root, "meta", "index.json"), "w") as f:
            json.dump(idx, f, indent=2)

    def _load_index(self):
        idx_path = os.path.join(self.root, "meta", "index.json")
        if os.path.exists(idx_path):
            with open(idx_path) as f:
                raw = json.load(f)
            for cid, d in raw.items():
                self._index[cid] = ATCObject(**d)


# ══════════════════════════════════════════════════════════════════════════════
# Singletons & Backwards-Compat
# ══════════════════════════════════════════════════════════════════════════════

_atcfs_vfs: Optional[ATCFileSystem] = None
_atcfs_store: Optional[ATCFS] = None


def get_vfs(owner: str = "system") -> ATCFileSystem:
    global _atcfs_vfs
    if _atcfs_vfs is None:
        _atcfs_vfs = ATCFileSystem(owner=owner)
    return _atcfs_vfs


def get_atcfs(root: str = ATCFS_ROOT) -> ATCFS:
    global _atcfs_store
    if _atcfs_store is None:
        _atcfs_store = ATCFS(root=root)
    return _atcfs_store
