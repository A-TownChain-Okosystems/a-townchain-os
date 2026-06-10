"""
MultiSig Wallet — Issue #24 (Kap. 38)
Multi-Signature Wallet für Bridge & Franchise Vault.
M-of-N Schema: Transaktion braucht M von N Signaturen.
"""
import hashlib, time, json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from enum import Enum

class TxStatus(Enum):
    PENDING   = "pending"
    APPROVED  = "approved"
    EXECUTED  = "executed"
    REJECTED  = "rejected"
    EXPIRED   = "expired"

@dataclass
class MultiSigTx:
    id:          str
    to:          str
    amount:      float
    token:       str            # "ATC" | "ETH" | "SOL" | ...
    data:        dict           # Optionale Payload (z.B. Bridge-Parameter)
    proposer:    str
    created:     float
    expires:     float
    status:      TxStatus = TxStatus.PENDING
    signatures:  Dict[str, str] = field(default_factory=dict)  # owner → sig
    executed_at: Optional[float] = None
    tx_hash:     Optional[str] = None

    def sign_hash(self) -> str:
        payload = f"{self.id}{self.to}{self.amount}{self.token}{self.proposer}"
        return hashlib.sha256(payload.encode()).hexdigest()

class MultiSigWallet:
    """
    M-of-N Multi-Signature Wallet.
    Anwendungen:
    - Bridge Vault: ATC ↔ ETH/SOL Lock/Release (M=2, N=3)
    - Franchise Vault: Franchise-Einnahmen (M=3, N=5)
    - DAO Treasury: Governance-Schatzkammer (M=5, N=9)
    """
    TX_EXPIRY = 7 * 86400   # 7 Tage

    def __init__(self, name: str, owners: List[str],
                 required_sigs: int, wallet_type: str = "generic"):
        if required_sigs > len(owners):
            raise ValueError(f"required_sigs ({required_sigs}) > owners ({len(owners)})")
        if required_sigs < 1:
            raise ValueError("required_sigs muss >= 1 sein")
        self.name          = name
        self.owners:       Set[str] = set(owners)
        self.required_sigs = required_sigs
        self.wallet_type   = wallet_type
        self._txs:         Dict[str, MultiSigTx] = {}
        self._balances:    Dict[str, float] = {}

    def _tx_id(self, to, amount, proposer) -> str:
        return hashlib.sha256(f"{to}{amount}{proposer}{time.time()}".encode()).hexdigest()[:16]

    def deposit(self, token: str, amount: float) -> float:
        self._balances[token] = self._balances.get(token, 0.0) + amount
        return self._balances[token]

    def balance(self, token: str = "ATC") -> float:
        return self._balances.get(token, 0.0)

    def propose(self, proposer: str, to: str, amount: float,
                 token: str = "ATC", data: dict = None) -> MultiSigTx:
        if proposer not in self.owners:
            raise PermissionError(f"{proposer} ist kein Wallet-Owner")
        bal = self._balances.get(token, 0.0)
        if amount > bal:
            raise ValueError(f"Nicht genug {token} (Vault: {bal}, gewünscht: {amount})")

        tx_id = self._tx_id(to, amount, proposer)
        tx = MultiSigTx(
            id=tx_id, to=to, amount=amount, token=token,
            data=data or {}, proposer=proposer,
            created=time.time(), expires=time.time() + self.TX_EXPIRY,
        )
        # Proposer unterschreibt automatisch
        tx.signatures[proposer] = hashlib.sha256(
            f"{tx.sign_hash()}{proposer}".encode()).hexdigest()[:32]
        self._txs[tx_id] = tx
        return tx

    def sign(self, tx_id: str, signer: str) -> bool:
        tx = self._txs.get(tx_id)
        if not tx: raise ValueError("TX nicht gefunden")
        if tx.status != TxStatus.PENDING: raise ValueError(f"TX ist {tx.status.value}")
        if time.time() > tx.expires: tx.status = TxStatus.EXPIRED; raise ValueError("TX abgelaufen")
        if signer not in self.owners: raise PermissionError(f"{signer} kein Owner")
        if signer in tx.signatures: raise ValueError(f"{signer} hat bereits signiert")

        tx.signatures[signer] = hashlib.sha256(
            f"{tx.sign_hash()}{signer}".encode()).hexdigest()[:32]

        if len(tx.signatures) >= self.required_sigs:
            tx.status = TxStatus.APPROVED
        return True

    def execute(self, tx_id: str, executor: str) -> dict:
        tx = self._txs.get(tx_id)
        if not tx: raise ValueError("TX nicht gefunden")
        if tx.status != TxStatus.APPROVED:
            raise ValueError(f"TX noch nicht approved (Status: {tx.status.value})")
        if executor not in self.owners:
            raise PermissionError(f"{executor} kein Owner")

        # Vault-Balance abziehen
        self._balances[tx.token] -= tx.amount
        tx.status      = TxStatus.EXECUTED
        tx.executed_at = time.time()
        tx.tx_hash     = hashlib.sha256(
            f"{tx_id}{executor}{tx.executed_at}".encode()).hexdigest()

        return {
            "tx_hash": tx.tx_hash, "from_vault": self.name,
            "to": tx.to, "amount": tx.amount, "token": tx.token,
            "executed_by": executor, "at": tx.executed_at,
            "signatures": list(tx.signatures.keys()),
        }

    def reject(self, tx_id: str, rejecter: str) -> bool:
        tx = self._txs.get(tx_id)
        if not tx or tx.status != TxStatus.PENDING: return False
        if rejecter not in self.owners: raise PermissionError("Kein Owner")
        tx.status = TxStatus.REJECTED
        return True

    def pending_txs(self) -> List[MultiSigTx]:
        return [t for t in self._txs.values() if t.status == TxStatus.PENDING]

    def stats(self) -> dict:
        txs = list(self._txs.values())
        return {
            "name": self.name, "type": self.wallet_type,
            "owners": len(self.owners), "required_sigs": self.required_sigs,
            "balances": self._balances,
            "total_txs": len(txs),
            "pending":  sum(1 for t in txs if t.status==TxStatus.PENDING),
            "executed": sum(1 for t in txs if t.status==TxStatus.EXECUTED),
        }


# ── Vordefinierte Vaults ────────────────────────────────────────────────
def create_bridge_vault(owners: List[str]) -> MultiSigWallet:
    """ATC ↔ EVM Bridge Vault — 2-of-3."""
    return MultiSigWallet("BridgeVault", owners, required_sigs=2,
                           wallet_type="bridge")

def create_franchise_vault(owners: List[str]) -> MultiSigWallet:
    """Franchise-Einnahmen Vault — 3-of-5."""
    return MultiSigWallet("FranchiseVault", owners, required_sigs=3,
                           wallet_type="franchise")

def create_dao_treasury(owners: List[str]) -> MultiSigWallet:
    """DAO Treasury — 5-of-9."""
    n = len(owners)
    m = max(1, (n // 2) + 1)   # Einfache Mehrheit
    return MultiSigWallet("DAOTreasury", owners, required_sigs=m,
                           wallet_type="treasury")
