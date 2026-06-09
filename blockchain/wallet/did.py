"""
DID-Resolver — ATAUTH-1000 Standard
did:kai:<account_id_hash>
Vollständige DID-Erzeugung, Auflösung und Verifikation.
"""
import hashlib, json, time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

DID_METHOD = "kai"

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

@dataclass
class DIDDocument:
    did:              str
    public_key:       str
    controller:       str
    created:          float = field(default_factory=time.time)
    updated:          float = field(default_factory=time.time)
    service_endpoints: List[dict] = field(default_factory=list)
    capabilities:     List[str]   = field(default_factory=list)
    revoked:          bool = False

    def to_dict(self): return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

class DIDResolver:
    """
    Dezentraler DID-Resolver für das A-TownChain Ökosystem.
    did:kai:<sha256(public_key)[:32]>
    """

    def __init__(self):
        self._registry: Dict[str, DIDDocument] = {}

    # ── DID erzeugen ──────────────────────────────────────
    @staticmethod
    def create_did(public_key: str) -> str:
        """DID aus Public Key ableiten."""
        identifier = _sha256(f"did:{DID_METHOD}:{public_key}")[:32]
        return f"did:{DID_METHOD}:{identifier}"

    def register(self, public_key: str,
                 capabilities: Optional[List[str]] = None,
                 service_endpoints: Optional[List[dict]] = None) -> DIDDocument:
        """DID registrieren und DIDDocument anlegen."""
        did = self.create_did(public_key)
        doc = DIDDocument(
            did               = did,
            public_key        = public_key,
            controller        = did,
            capabilities      = capabilities or ["auth", "sign", "encrypt"],
            service_endpoints = service_endpoints or [],
        )
        self._registry[did] = doc
        return doc

    # ── DID auflösen ──────────────────────────────────────
    def resolve(self, did: str) -> Optional[DIDDocument]:
        """DID → DIDDocument."""
        return self._registry.get(did)

    def resolve_json(self, did: str) -> Optional[str]:
        doc = self.resolve(did)
        return doc.to_json() if doc else None

    # ── DID verifizieren ──────────────────────────────────
    def verify(self, did: str, public_key: str) -> bool:
        """Prüft ob DID zu diesem Public Key gehört."""
        doc = self.resolve(did)
        if not doc or doc.revoked:
            return False
        expected = self.create_did(public_key)
        return expected == did and doc.public_key == public_key

    # ── DID widerrufen ────────────────────────────────────
    def revoke(self, did: str) -> bool:
        doc = self.resolve(did)
        if not doc: return False
        doc.revoked = True
        doc.updated = time.time()
        return True

    # ── Update ────────────────────────────────────────────
    def update(self, did: str,
               capabilities: Optional[List[str]] = None,
               service_endpoints: Optional[List[dict]] = None) -> bool:
        doc = self.resolve(did)
        if not doc or doc.revoked: return False
        if capabilities:      doc.capabilities      = capabilities
        if service_endpoints: doc.service_endpoints = service_endpoints
        doc.updated = time.time()
        return True

    def list_dids(self) -> List[str]:
        return list(self._registry.keys())

    def stats(self) -> dict:
        total   = len(self._registry)
        revoked = sum(1 for d in self._registry.values() if d.revoked)
        return {"total": total, "active": total - revoked, "revoked": revoked}
