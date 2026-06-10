"""
Cross-Chain Bridge — Issue #10 (ATC ↔ EVM Interoperabilität)
Lock-and-Mint Bridge: ATC ↔ Ethereum/Polygon/BSC.
"""
import hashlib, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class BridgeChain(Enum):
    ATC      = "atc"
    ETHEREUM = "ethereum"
    POLYGON  = "polygon"
    BSC      = "bsc"
    SOLANA   = "solana"

class BridgeTxStatus(Enum):
    INITIATED  = "initiated"
    LOCKED     = "locked"
    RELAYED    = "relayed"
    MINTED     = "minted"
    COMPLETED  = "completed"
    FAILED     = "failed"
    REFUNDED   = "refunded"

@dataclass
class BridgeTx:
    id:           str
    from_chain:   BridgeChain
    to_chain:     BridgeChain
    from_address: str
    to_address:   str
    amount:       float
    token:        str   # "ATC" | "WATC" (Wrapped ATC)
    status:       BridgeTxStatus = BridgeTxStatus.INITIATED
    lock_hash:    Optional[str] = None
    mint_hash:    Optional[str] = None
    created:      float = field(default_factory=time.time)
    completed:    Optional[float] = None
    fee:          float = 0.0
    relayer:      Optional[str] = None

class CrossChainBridge:
    """
    A-TownChain ↔ EVM Cross-Chain Bridge (ATC-BRIDGE-1000).
    Mechanismus:
    1. ATC → EVM: Lock ATC im Bridge-Vault → Mint WATC auf Ziel-Chain
    2. EVM → ATC: Burn WATC auf Quell-Chain → Release ATC aus Vault
    3. Relayer-Netzwerk: Validiert Events + übermittelt Proofs
    """
    BRIDGE_FEE  = 0.003   # 0.3% Bridge-Gebühr
    MIN_AMOUNT  = 10.0    # Min 10 ATC
    MAX_AMOUNT  = 100_000.0
    RELAY_DELAY = 180     # ~3 Minuten

    # Unterstützte Token-Paare
    SUPPORTED_PAIRS = {
        (BridgeChain.ATC, BridgeChain.ETHEREUM): ("ATC", "WATC"),
        (BridgeChain.ATC, BridgeChain.POLYGON):  ("ATC", "WATC"),
        (BridgeChain.ATC, BridgeChain.BSC):      ("ATC", "WATC"),
        (BridgeChain.ETHEREUM, BridgeChain.ATC): ("WATC","ATC"),
        (BridgeChain.POLYGON,  BridgeChain.ATC): ("WATC","ATC"),
    }

    def __init__(self, multisig_vault=None):
        self._txs:     Dict[str, BridgeTx] = {}
        self._vault    = multisig_vault      # MultiSigWallet für Lock
        self._locked:  float = 0.0
        self._relayers: List[str] = []
        self._total_volume: float = 0.0

    def add_relayer(self, relayer_id: str):
        if relayer_id not in self._relayers:
            self._relayers.append(relayer_id)

    def _tx_id(self, from_addr, to_addr, amount) -> str:
        return hashlib.sha256(f"{from_addr}{to_addr}{amount}{time.time()}".encode()).hexdigest()[:16]

    def initiate(self, from_chain: BridgeChain, to_chain: BridgeChain,
                  from_addr: str, to_addr: str, amount: float) -> BridgeTx:
        """Schritt 1: Bridge-Transaktion initiieren."""
        pair = (from_chain, to_chain)
        if pair not in self.SUPPORTED_PAIRS:
            raise ValueError(f"Pair {from_chain.value}→{to_chain.value} nicht unterstützt")
        if amount < self.MIN_AMOUNT:
            raise ValueError(f"Minimum {self.MIN_AMOUNT} ATC")
        if amount > self.MAX_AMOUNT:
            raise ValueError(f"Maximum {self.MAX_AMOUNT} ATC pro Transaktion")

        fee = round(amount * self.BRIDGE_FEE, 6)
        src_token, dst_token = self.SUPPORTED_PAIRS[pair]

        tx_id = self._tx_id(from_addr, to_addr, amount)
        tx = BridgeTx(
            id=tx_id, from_chain=from_chain, to_chain=to_chain,
            from_address=from_addr, to_address=to_addr,
            amount=amount, token=src_token, fee=fee,
        )
        self._txs[tx_id] = tx
        return tx

    def lock(self, tx_id: str, lock_proof: str) -> BridgeTx:
        """Schritt 2: Token auf Quell-Chain gesperrt."""
        tx = self._txs.get(tx_id)
        if not tx: raise ValueError("TX nicht gefunden")
        if tx.status != BridgeTxStatus.INITIATED:
            raise ValueError("TX nicht im INITIATED Status")
        tx.lock_hash = hashlib.sha256(f"{lock_proof}{tx_id}".encode()).hexdigest()
        tx.status    = BridgeTxStatus.LOCKED
        self._locked += tx.amount
        return tx

    def relay(self, tx_id: str, relayer: str) -> BridgeTx:
        """Schritt 3: Relayer bestätigt Lock → leitet an Ziel-Chain weiter."""
        tx = self._txs.get(tx_id)
        if not tx: raise ValueError("TX nicht gefunden")
        if tx.status != BridgeTxStatus.LOCKED:
            raise ValueError("TX noch nicht LOCKED")
        if relayer not in self._relayers and self._relayers:
            raise PermissionError(f"{relayer} ist kein autorisierter Relayer")
        tx.relayer = relayer
        tx.status  = BridgeTxStatus.RELAYED
        return tx

    def mint(self, tx_id: str, mint_proof: str) -> BridgeTx:
        """Schritt 4: WATC auf Ziel-Chain gemint."""
        tx = self._txs.get(tx_id)
        if not tx: raise ValueError("TX nicht gefunden")
        if tx.status != BridgeTxStatus.RELAYED:
            raise ValueError("TX noch nicht RELAYED")
        tx.mint_hash  = hashlib.sha256(f"{mint_proof}{tx_id}".encode()).hexdigest()
        tx.status     = BridgeTxStatus.COMPLETED
        tx.completed  = time.time()
        self._total_volume += tx.amount
        net_amount = tx.amount - tx.fee
        return tx

    def refund(self, tx_id: str, reason: str) -> BridgeTx:
        """Fehlgeschlagene TX rückerstatten."""
        tx = self._txs.get(tx_id)
        if not tx: raise ValueError("TX nicht gefunden")
        if tx.status in (BridgeTxStatus.COMPLETED, BridgeTxStatus.REFUNDED):
            raise ValueError("TX kann nicht mehr erstattet werden")
        if tx.status == BridgeTxStatus.LOCKED:
            self._locked -= tx.amount
        tx.status = BridgeTxStatus.REFUNDED
        return tx

    def stats(self) -> dict:
        txs = list(self._txs.values())
        return {
            "total_txs":     len(txs),
            "completed":     sum(1 for t in txs if t.status==BridgeTxStatus.COMPLETED),
            "pending":       sum(1 for t in txs if t.status not in (BridgeTxStatus.COMPLETED, BridgeTxStatus.FAILED, BridgeTxStatus.REFUNDED)),
            "total_volume":  round(self._total_volume, 2),
            "locked_atc":    round(self._locked, 2),
            "relayers":      len(self._relayers),
            "supported_pairs": [f"{a.value}→{b.value}" for a,b in self.SUPPORTED_PAIRS],
        }
