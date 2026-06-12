"""
KAI-OS Kernel — ATCFS (A-TownChain Filesystem)
Dezentrales, content-adressiertes Dateisystem auf IPFS-Basis.
Wiki: Kap. 58
"""
import hashlib
import os
import json
import time
import threading
import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List

logger = logging.getLogger("kernel.atcfs")

ATCFS_ROOT = os.path.join(os.path.expanduser("~"), ".atcfs")


@dataclass
class ATCFile:
    cid: str          # Content-ID (SHA256 des Inhalts)
    name: str
    size: int
    content_hash: str
    created_at: float = field(default_factory=time.time)
    pinned: bool = False
    tags: List[str] = field(default_factory=list)


class ATCFS:
    """A-TownChain Filesystem — content-addressed, decentralized storage."""

    def __init__(self, root: str = ATCFS_ROOT):
        self.root = root
        self._index: Dict[str, ATCFile] = {}
        self._lock = threading.Lock()
        os.makedirs(os.path.join(root, "objects"), exist_ok=True)
        os.makedirs(os.path.join(root, "meta"), exist_ok=True)
        self._load_index()
        logger.info(f"ATCFS initialized at {root} ({len(self._index)} files)")

    def _cid(self, data: bytes) -> str:
        return "atcfs://" + hashlib.sha256(data).hexdigest()

    def _obj_path(self, cid: str) -> str:
        h = cid.replace("atcfs://", "")
        return os.path.join(self.root, "objects", h[:2], h[2:])

    def write(self, name: str, data: bytes, tags: List[str] = None) -> str:
        """Write data and return CID."""
        cid = self._cid(data)
        obj_path = self._obj_path(cid)
        os.makedirs(os.path.dirname(obj_path), exist_ok=True)
        if not os.path.exists(obj_path):
            with open(obj_path, "wb") as f:
                f.write(data)
        atcfile = ATCFile(
            cid=cid, name=name, size=len(data),
            content_hash=cid.replace("atcfs://", ""),
            tags=tags or []
        )
        with self._lock:
            self._index[cid] = atcfile
        self._save_index()
        logger.debug(f"ATCFS.write: {name} -> {cid[:20]}...")
        return cid

    def read(self, cid: str) -> Optional[bytes]:
        """Read data by CID."""
        obj_path = self._obj_path(cid)
        if not os.path.exists(obj_path):
            logger.warning(f"ATCFS.read: CID not found: {cid[:20]}")
            return None
        with open(obj_path, "rb") as f:
            return f.read()

    def exists(self, cid: str) -> bool:
        return cid in self._index

    def pin(self, cid: str) -> bool:
        """Pin a file (prevent garbage collection)."""
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

    def list_files(self, tag: str = None) -> List[Dict]:
        with self._lock:
            files = list(self._index.values())
        if tag:
            files = [f for f in files if tag in f.tags]
        return [
            {"cid": f.cid, "name": f.name, "size": f.size,
             "pinned": f.pinned, "tags": f.tags,
             "created": time.strftime("%Y-%m-%d", time.localtime(f.created_at))}
            for f in files
        ]

    def delete(self, cid: str, force: bool = False) -> bool:
        with self._lock:
            atcfile = self._index.get(cid)
        if not atcfile:
            return False
        if atcfile.pinned and not force:
            logger.warning(f"Cannot delete pinned file {cid[:20]}")
            return False
        obj_path = self._obj_path(cid)
        if os.path.exists(obj_path):
            os.remove(obj_path)
        with self._lock:
            del self._index[cid]
        self._save_index()
        return True

    def _save_index(self):
        idx = {cid: {
            "cid": f.cid, "name": f.name, "size": f.size,
            "content_hash": f.content_hash, "created_at": f.created_at,
            "pinned": f.pinned, "tags": f.tags
        } for cid, f in self._index.items()}
        with open(os.path.join(self.root, "meta", "index.json"), "w") as f:
            json.dump(idx, f, indent=2)

    def _load_index(self):
        idx_path = os.path.join(self.root, "meta", "index.json")
        if os.path.exists(idx_path):
            with open(idx_path) as f:
                raw = json.load(f)
            for cid, d in raw.items():
                self._index[cid] = ATCFile(**d)

    def stats(self) -> Dict:
        with self._lock:
            files = list(self._index.values())
        return {
            "total_files": len(files),
            "total_size_bytes": sum(f.size for f in files),
            "pinned": sum(1 for f in files if f.pinned),
            "root": self.root,
        }


_atcfs = ATCFS()

def get_atcfs() -> ATCFS:
    return _atcfs
