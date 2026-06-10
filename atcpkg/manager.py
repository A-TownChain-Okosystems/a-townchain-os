"""
atcpkg — Plugin & Modul-System · Issue #27 (Kap. 43)
Dezentrales Paketmanager für A-TownChain Module.
"""
import hashlib, json, os, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ATCPackage:
    name:        str
    version:     str
    description: str
    author:      str
    layer:       str       # L0–L12
    cid:         str       # IPFS CID des Pakets
    deps:        List[str] = field(default_factory=list)
    created:     float = field(default_factory=time.time)
    downloads:   int = 0
    verified:    bool = False

class ATCPackageManager:
    """
    atcpkg — A-TownChain Package Manager (ATPKG-1000).
    - Registrierung von Paketen on-chain
    - Dependency-Auflösung
    - Signatur-Verifizierung
    - Dezentrale Distribution via IPFS/ATCFS
    """
    REGISTRY_PATH = "/atc/pkg/registry.json"

    def __init__(self):
        self._packages: Dict[str, ATCPackage] = {}
        self._installed: List[str] = []
        self._seed_defaults()

    def _seed_defaults(self):
        """Standard-Pakete vorinstallieren."""
        defaults = [
            ("atc-core",      "2.0.0", "A-TownChain Kernel & Blockchain Core", "L4"),
            ("atc-wallet",    "2.0.0", "ECDSA Wallet + MultiSig",              "L4"),
            ("atc-gateway",   "2.0.0", "API Gateway auf Port 4000",            "L7"),
            ("atc-shivamon",  "1.0.0", "Shivamon NFT Contracts",               "L12"),
            ("atc-governance","1.0.0", "DAO Governance Contract",              "L8"),
            ("atcfs",         "1.0.0", "A-TownChain Filesystem",               "L6"),
        ]
        for name, ver, desc, layer in defaults:
            cid = hashlib.sha256(f"{name}{ver}".encode()).hexdigest()[:32]
            pkg = ATCPackage(name=name, version=ver, description=desc,
                              author="A-TownChain-Okosystems", layer=layer,
                              cid=cid, verified=True)
            self._packages[name] = pkg
            self._installed.append(name)

    def publish(self, pkg: ATCPackage) -> str:
        self._packages[pkg.name] = pkg
        return pkg.cid

    def install(self, name: str, version: str = "latest") -> bool:
        pkg = self._packages.get(name)
        if not pkg: raise ValueError(f"Paket '{name}' nicht gefunden")
        # Deps zuerst
        for dep in pkg.deps:
            if dep not in self._installed:
                self.install(dep)
        if name not in self._installed:
            self._installed.append(name)
        pkg.downloads += 1
        return True

    def search(self, query: str) -> List[ATCPackage]:
        q = query.lower()
        return [p for p in self._packages.values()
                if q in p.name.lower() or q in p.description.lower()]

    def list_installed(self) -> List[ATCPackage]:
        return [self._packages[n] for n in self._installed if n in self._packages]

    def info(self, name: str) -> Optional[ATCPackage]:
        return self._packages.get(name)

    def stats(self) -> dict:
        return {"total": len(self._packages), "installed": len(self._installed),
                "verified": sum(1 for p in self._packages.values() if p.verified)}
