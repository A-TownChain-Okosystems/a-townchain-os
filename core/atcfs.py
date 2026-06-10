"""
ATCFS — A-TownChain Filesystem · Issue #23 (Kap. 45)
Dezentrales, verschlüsseltes Dateisystem auf L6 (Storage Layer).
Integration in ShivaOS Kernel und Blockchain-Nodes.
"""
import hashlib, time, json, os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum

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
    size:        int = 0
    content_cid: str = ""          # IPFS-CID oder lokaler Hash
    permissions: Dict[str, List[str]] = field(default_factory=dict)
    created:     float = field(default_factory=time.time)
    modified:    float = field(default_factory=time.time)
    children:    List[str] = field(default_factory=list)  # Pfade der Kind-Knoten
    encrypted:   bool = False
    merkle_hash: str = ""

    def __post_init__(self):
        if not self.merkle_hash:
            self.merkle_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        data = f"{self.name}{self.owner}{self.size}{self.content_cid}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

class ATCFileSystem:
    """
    A-TownChain Dateisystem (ATCFS).
    Standard: ATS-1001 Storage Layer.
    Integriert in: ShivaOS Kernel (L2) + P2P Nodes (L5) + Blockchain (L4).
    """
    ROOT = "/"

    def __init__(self, owner: str = "system"):
        self._nodes: Dict[str, ATCFSNode] = {}
        self._owner = owner
        self._init_root()

    def _init_root(self):
        root = ATCFSNode(name="/", path="/", is_dir=True, owner=self._owner,
                         permissions={"system": ["r","w","x","o"], "world": ["r","x"]})
        self._nodes["/"] = root
        for d in ["/home", "/tmp", "/var", "/var/log", "/var/data",
                  "/proc", "/sys", "/dev", "/mnt", "/atc", "/atc/contracts",
                  "/atc/wallets", "/atc/chain", "/atc/peers"]:
            self.mkdir(d, self._owner)

    def _resolve(self, path: str) -> str:
        """Pfad normalisieren."""
        parts = [p for p in path.split("/") if p]
        return "/" + "/".join(parts) if parts else "/"

    def _parent(self, path: str) -> str:
        r = self._resolve(path)
        parts = r.rstrip("/").rsplit("/", 1)
        return parts[0] if parts[0] else "/"

    def exists(self, path: str) -> bool:
        return self._resolve(path) in self._nodes

    def mkdir(self, path: str, owner: str, parents: bool = True) -> ATCFSNode:
        r = self._resolve(path)
        if r in self._nodes: return self._nodes[r]
        parent = self._parent(r)
        if parents and parent != r and parent not in self._nodes:
            self.mkdir(parent, owner, parents=True)
        node = ATCFSNode(name=r.rsplit("/",1)[-1] or "/", path=r,
                          is_dir=True, owner=owner,
                          permissions={owner: ["r","w","x","o"]})
        self._nodes[r] = node
        if parent in self._nodes and r not in self._nodes[parent].children:
            self._nodes[parent].children.append(r)
        return node

    def write(self, path: str, content: bytes, owner: str,
               encrypt: bool = False) -> ATCFSNode:
        r = self._resolve(path)
        parent = self._parent(r)
        if parent not in self._nodes:
            self.mkdir(parent, owner, parents=True)
        cid = hashlib.sha256(content).hexdigest()
        node = ATCFSNode(
            name=r.rsplit("/",1)[-1], path=r, is_dir=False,
            owner=owner, size=len(content), content_cid=cid,
            encrypted=encrypt, modified=time.time(),
            permissions={owner: ["r","w","o"]},
        )
        self._nodes[r] = node
        if r not in self._nodes[parent].children:
            self._nodes[parent].children.append(r)
        return node

    def read(self, path: str, requester: str) -> Tuple[str, ATCFSNode]:
        """CID zurückgeben (eigentlicher Inhalt via IPFS/lokaler Store)."""
        r = self._resolve(path)
        if r not in self._nodes: raise FileNotFoundError(f"Pfad nicht gefunden: {r}")
        node = self._nodes[r]
        perms = node.permissions.get(requester, node.permissions.get("world", []))
        if "r" not in perms and node.owner != requester:
            raise PermissionError(f"{requester} darf {r} nicht lesen")
        return node.content_cid, node

    def ls(self, path: str) -> List[ATCFSNode]:
        r = self._resolve(path)
        if r not in self._nodes: raise FileNotFoundError(r)
        node = self._nodes[r]
        if not node.is_dir: return [node]
        return [self._nodes[c] for c in node.children if c in self._nodes]

    def rm(self, path: str, owner: str, recursive: bool = False) -> bool:
        r = self._resolve(path)
        if r not in self._nodes: return False
        node = self._nodes[r]
        if node.owner != owner: raise PermissionError(f"Nur Owner darf löschen")
        if node.is_dir and node.children and not recursive:
            raise IsADirectoryError(f"Verzeichnis nicht leer — benutze recursive=True")
        if recursive:
            for child in list(node.children):
                self.rm(child, owner, recursive=True)
        parent = self._parent(r)
        if parent in self._nodes:
            self._nodes[parent].children = [c for c in self._nodes[parent].children if c != r]
        del self._nodes[r]
        return True

    def stat(self) -> dict:
        dirs  = sum(1 for n in self._nodes.values() if n.is_dir)
        files = sum(1 for n in self._nodes.values() if not n.is_dir)
        total = sum(n.size for n in self._nodes.values())
        return {"total_nodes": len(self._nodes), "directories": dirs,
                "files": files, "total_bytes": total}

    def mount(self, mountpoint: str, remote_cid: str, owner: str) -> ATCFSNode:
        """Remote ATCFS (via CID) einbinden."""
        mp = self._resolve(mountpoint)
        self.mkdir(mp, owner)
        marker = self.write(f"{mp}/.atcfs_mount", remote_cid.encode(), owner)
        return marker

    def export_manifest(self) -> dict:
        """Kompletten FS-Baum als JSON-Manifest exportieren (für Blockchain-Anchoring)."""
        manifest = {}
        for path, node in self._nodes.items():
            manifest[path] = {
                "name": node.name, "is_dir": node.is_dir,
                "owner": node.owner, "size": node.size,
                "cid": node.content_cid, "hash": node.merkle_hash,
                "modified": node.modified,
            }
        root_hash = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
        return {"root_hash": root_hash, "entries": len(manifest), "fs": manifest}
