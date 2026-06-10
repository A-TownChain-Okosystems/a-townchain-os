"""
core/atcfs.py — ATCFS: A-TownChain Dezentrales Dateisystem
ATS-1002 Standard — Layer L6 Storage

Konzept:
  - Content-Adressierung via SHA-256 (CID)
  - Dezentrale Replikation (min. 3 Kopien)
  - Adress-Syntax: atcfs://<node_id>/<cid>/<path>
  - Integriert in ShivaOS — transparenter Zugriff
  - On-Chain Metadaten (INODE-Hashes)

Dateitypen:
  .atc  = ATCLang Quellcode
  .atcb = Bytecode (kompiliert)
  .atcm = Modul (signiert)
  .atcw = Wallet (verschlüsselt)
  .atcd = ATC-Daten
  .atcp = Prozess-Image
"""
import hashlib
import time
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Tuple
from enum import Enum


# ── Typen ─────────────────────────────────────────────────────────────────────

class FileType(Enum):
    FILE     = "FILE"
    DIR      = "DIR"
    SYMLINK  = "SYMLINK"
    CONTRACT = "CONTRACT"


@dataclass
class INode:
    """ATCFS INODE — Metadaten-Eintrag für eine Datei oder ein Verzeichnis."""
    cid:          str            # SHA-256(content) — Content-Hash
    name:         str            # Dateiname
    size:         int            # Bytes
    owner:        str            # ATC-Adresse des Eigentümers
    created:      int            # Unix-Timestamp
    modified:     int            # Letzter Schreibzugriff
    perms:        str = "rw-r--r--"  # POSIX-ähnliche Berechtigungen
    type:         str = FileType.FILE.value
    replicas:     int = 0        # Aktuelle Replikas
    min_replicas: int = 3        # Mindest-Replikas
    encrypted:    bool = False
    tags:         List[str] = field(default_factory=list)
    parent_cid:   Optional[str] = None   # Für DIR-Einträge

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class FileHandle:
    """Offener Datei-Handle (ähnlich POSIX fd)."""
    fh_id:    int
    cid:      str
    mode:     str       # "r", "w", "a"
    offset:   int = 0
    dirty:    bool = False


# ── ATCFS Hauptklasse ─────────────────────────────────────────────────────────

class ATCFS:
    """
    A-TownChain File System (ATCFS) — ATS-1002

    Lokales Single-Node-Subsystem.
    Für Multi-Node-Replikation: ATCNet-Integration (modules/atcnet/).
    """

    VERSION = "1.0.0"
    ADDR_SCHEME = "atcfs://"

    def __init__(self, root_dir: str = "data/atcfs", node_id: str = "local"):
        self._root     = root_dir
        self._node_id  = node_id
        self._inodes:  Dict[str, INode]       = {}   # cid → INode
        self._blocks:  Dict[str, bytes]       = {}   # cid → Inhalt
        self._dirs:    Dict[str, List[str]]   = {}   # dir_cid → [child_cid, ...]
        self._handles: Dict[int, FileHandle]  = {}
        self._next_fh  = 1
        self._next_peer_id = 0
        os.makedirs(root_dir, exist_ok=True)

    # ── Kern-API (Kernel-Interface ATS-1000) ──────────────────────────────────

    def write(self, data: bytes, name: str, owner: str,
               ftype: FileType = FileType.FILE,
               perms: str = "rw-r--r--",
               tags: list = None,
               encrypt: bool = False,
               parent_cid: str = None) -> str:
        """
        Datei schreiben / überschreiben.
        Gibt CID (SHA-256 Content-Hash) zurück.
        """
        cid = self._sha256(data)
        now = int(time.time())

        inode = INode(
            cid          = cid,
            name         = name,
            size         = len(data),
            owner        = owner,
            created      = now,
            modified     = now,
            perms        = perms,
            type         = ftype.value,
            replicas     = 1,
            min_replicas = 3,
            encrypted    = encrypt,
            tags         = tags or [],
            parent_cid   = parent_cid,
        )
        self._blocks[cid] = data
        self._inodes[cid] = inode

        # Persistenz
        self._persist_block(cid, data)
        self._persist_inode(cid, inode)

        return cid

    def read(self, cid: str) -> bytes:
        """Datei über CID lesen."""
        if cid in self._blocks:
            return self._blocks[cid]
        # Von Disk laden
        data = self._load_block(cid)
        if data is not None:
            self._blocks[cid] = data
            return data
        raise FileNotFoundError(f"ATCFS: CID {cid} nicht gefunden")

    def delete(self, cid: str, caller: str) -> bool:
        """Datei löschen (nur Owner oder root)."""
        inode = self._inodes.get(cid)
        if not inode:
            return False
        if inode.owner != caller and caller != "root":
            raise PermissionError(f"ATCFS: {caller} hat keinen Schreibzugriff auf {cid}")
        del self._inodes[cid]
        if cid in self._blocks:
            del self._blocks[cid]
        self._delete_block(cid)
        return True

    # ── POSIX-ähnliche File-Handle API ───────────────────────────────────────

    def open(self, atcfs_url: str, mode: str = "r") -> FileHandle:
        """
        Öffnet eine ATCFS-URL als File-Handle.
        URL-Format: atcfs://<node_id>/<cid>
        """
        cid = self._url_to_cid(atcfs_url)
        fh  = FileHandle(fh_id=self._next_fh, cid=cid, mode=mode)
        self._handles[self._next_fh] = fh
        self._next_fh += 1
        return fh

    def read_fh(self, fh: FileHandle, size: int = -1) -> bytes:
        """Liest über File-Handle (mit Offset-Tracking)."""
        assert fh.mode in ("r", "a"), "File-Handle nicht im Lesemodus"
        data   = self.read(fh.cid)
        if size < 0:
            chunk  = data[fh.offset:]
        else:
            chunk  = data[fh.offset: fh.offset + size]
        fh.offset += len(chunk)
        return chunk

    def write_fh(self, fh: FileHandle, data: bytes) -> int:
        """Schreibt über File-Handle."""
        assert fh.mode in ("w", "a"), "File-Handle nicht im Schreibmodus"
        fh.dirty = True
        existing  = self._blocks.get(fh.cid, b"")
        if fh.mode == "a":
            new_data = existing + data
        else:
            new_data = data
        new_cid   = self._sha256(new_data)
        self._blocks[new_cid] = new_data
        fh.cid    = new_cid
        fh.offset += len(data)
        return len(data)

    def close(self, fh: FileHandle):
        """File-Handle schließen und ggf. persistieren."""
        if fh.dirty and fh.cid in self._blocks:
            self._persist_block(fh.cid, self._blocks[fh.cid])
        if fh.fh_id in self._handles:
            del self._handles[fh.fh_id]

    # ── Verzeichnis-API ────────────────────────────────────────────────────────

    def mkdir(self, name: str, owner: str, parent_cid: str = None) -> str:
        """Verzeichnis anlegen, CID zurückgeben."""
        meta_bytes = json.dumps({
            "name": name, "type": "DIR",
            "owner": owner, "created": int(time.time())
        }).encode()
        cid = self.write(meta_bytes, name, owner,
                          ftype=FileType.DIR, parent_cid=parent_cid)
        self._dirs[cid] = []
        return cid

    def listdir(self, dir_cid: str) -> List[INode]:
        """Verzeichnis-Inhalt auflisten."""
        children = self._dirs.get(dir_cid, [])
        return [self._inodes[c] for c in children if c in self._inodes]

    # ── Metadaten & Suche ──────────────────────────────────────────────────────

    def stat(self, cid: str) -> Optional[INode]:
        """INODE-Metadaten abrufen."""
        if cid in self._inodes:
            return self._inodes[cid]
        return self._load_inode(cid)

    def find(self, owner: str = None, tags: list = None,
              ftype: str = None) -> List[INode]:
        """Dateien nach Owner, Tags oder Typ suchen."""
        results = list(self._inodes.values())
        if owner:
            results = [i for i in results if i.owner == owner]
        if tags:
            results = [i for i in results
                       if any(t in i.tags for t in tags)]
        if ftype:
            results = [i for i in results if i.type == ftype]
        return results

    def get_stats(self) -> dict:
        """ATCFS-Gesamtstatistik."""
        total_size = sum(i.size for i in self._inodes.values())
        return {
            "version":       self.VERSION,
            "node_id":       self._node_id,
            "total_files":   len(self._inodes),
            "total_dirs":    len(self._dirs),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "blocks_cached": len(self._blocks),
            "open_handles":  len(self._handles),
        }

    # ── URL-Helfer ─────────────────────────────────────────────────────────────

    def build_url(self, cid: str) -> str:
        """Baut ATCFS-URL: atcfs://<node_id>/<cid>"""
        return f"{self.ADDR_SCHEME}{self._node_id}/{cid}"

    def _url_to_cid(self, url: str) -> str:
        """Extrahiert CID aus ATCFS-URL."""
        if url.startswith(self.ADDR_SCHEME):
            parts = url[len(self.ADDR_SCHEME):].split("/")
            return parts[1] if len(parts) > 1 else parts[0]
        return url  # Direkte CID-Übergabe

    # ── Persistenz ─────────────────────────────────────────────────────────────

    def _persist_block(self, cid: str, data: bytes):
        path = os.path.join(self._root, "blocks", cid[:2])
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, cid), "wb") as f:
            f.write(data)

    def _load_block(self, cid: str) -> Optional[bytes]:
        path = os.path.join(self._root, "blocks", cid[:2], cid)
        if os.path.exists(path):
            with open(path, "rb") as f:
                return f.read()
        return None

    def _delete_block(self, cid: str):
        path = os.path.join(self._root, "blocks", cid[:2], cid)
        if os.path.exists(path):
            os.remove(path)

    def _persist_inode(self, cid: str, inode: INode):
        path = os.path.join(self._root, "inodes")
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, cid + ".json"), "w") as f:
            json.dump(inode.to_dict(), f)

    def _load_inode(self, cid: str) -> Optional[INode]:
        path = os.path.join(self._root, "inodes", cid + ".json")
        if os.path.exists(path):
            with open(path) as f:
                d = json.load(f)
            return INode(**d)
        return None

    # ── Interne Hilfsmethoden ──────────────────────────────────────────────────

    @staticmethod
    def _sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


# ── Singleton ──────────────────────────────────────────────────────────────────
_atcfs_instance: Optional[ATCFS] = None

def get_atcfs(root_dir: str = "data/atcfs", node_id: str = "local") -> ATCFS:
    """Globale ATCFS-Instanz (Singleton)."""
    global _atcfs_instance
    if _atcfs_instance is None:
        _atcfs_instance = ATCFS(root_dir, node_id)
    return _atcfs_instance
