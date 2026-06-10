"""
blockchain/wallet/multisig.py — ATC Multi-Sig Wallet
ATS-1003 Standard — M-of-N Threshold Signature Scheme

Einsatzgebiete:
  - Bridge Vault (3-of-5 Relayer)
  - Franchise Vault (2-of-3 Founder/DAO/Treasury)
  - DAO Treasury (5-of-9 Council)
  - Enterprise Wallets (N-of-M)

Ablauf:
  1. propose_tx()    → TX vorschlagen, TX-ID zurück
  2. sign_tx()       → Signatur hinzufügen (pro Mitglied)
  3. execute_tx()    → Ausführen wenn Threshold erreicht
  4. cancel_tx()     → Owner kann TX canceln
"""
import hashlib
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from enum import Enum


# ── Typen ─────────────────────────────────────────────────────────────────────

class TxStatus(Enum):
    PENDING   = "pending"      # Warte auf Signaturen
    READY     = "ready"        # Threshold erreicht, ausführbar
    EXECUTED  = "executed"     # Ausgeführt
    CANCELLED = "cancelled"    # Abgebrochen
    EXPIRED   = "expired"      # Timeout abgelaufen


@dataclass
class MultiSigTx:
    """Eine vorgeschlagene Multi-Sig-Transaktion."""
    tx_id:       str
    proposer:    str           # ATC-Adresse des Vorschlagenden
    to:          str           # Empfänger
    value:       float         # ATC-Betrag
    data:        bytes         # Optionale Call-Daten (für Contract-Calls)
    description: str           # Lesbarer Beschreibungstext
    created_at:  int           # Unix-Timestamp
    expires_at:  int           # Ablaufzeit (default: 7 Tage)
    status:      str = TxStatus.PENDING.value
    signatures:  Dict[str, str] = field(default_factory=dict)  # addr → sig
    executed_at: Optional[int] = None
    tx_hash:     Optional[str] = None   # On-Chain-Hash nach Execution

    def to_dict(self) -> dict:
        d = asdict(self)
        d["data"] = self.data.hex() if self.data else ""
        return d


# ── Multi-Sig Wallet ──────────────────────────────────────────────────────────

class MultiSigWallet:
    """
    M-of-N Threshold Wallet für A-TownChain.

    Beispiel (3-of-5 Bridge):
        wallet = MultiSigWallet(
            owners    = [r1, r2, r3, r4, r5],
            threshold = 3,
            name      = "ATC-Bridge-Vault"
        )
        tx_id = wallet.propose_tx(r1, "0xTargetAddr", 50000.0, b"", "Bridge-Transfer")
        wallet.sign_tx(r2, tx_id)
        wallet.sign_tx(r3, tx_id)
        result = wallet.execute_tx(tx_id, r1)
    """

    TX_TTL = 7 * 24 * 3600    # 7 Tage Gültigkeit

    def __init__(self, owners: List[str], threshold: int, name: str = "MultiSig"):
        if not owners:
            raise ValueError("Mindestens 1 Owner erforderlich")
        if threshold < 1 or threshold > len(owners):
            raise ValueError(f"Threshold {threshold} ungültig für {len(owners)} Owner")
        self.owners    = set(owners)
        self.threshold = threshold
        self.name      = name
        self._txs:     Dict[str, MultiSigTx] = {}
        self._balance  = 0.0    # Simuliertes ATC-Guthaben

    # ── TX vorschlagen ────────────────────────────────────────────────────────

    def propose_tx(self, proposer: str, to: str, value: float,
                   data: bytes = b"", description: str = "") -> str:
        """
        Neue TX vorschlagen. Proposer unterschreibt automatisch.
        Gibt tx_id zurück.
        """
        if proposer not in self.owners:
            raise PermissionError(f"{proposer} ist kein Owner")
        if value < 0:
            raise ValueError("Negativer Betrag nicht erlaubt")

        now   = int(time.time())
        tx_id = self._make_tx_id(proposer, to, value, now)

        tx = MultiSigTx(
            tx_id       = tx_id,
            proposer    = proposer,
            to          = to,
            value       = value,
            data        = data,
            description = description,
            created_at  = now,
            expires_at  = now + self.TX_TTL,
        )
        # Proposer unterschreibt automatisch
        tx.signatures[proposer] = self._sign(proposer, tx_id, now)
        self._txs[tx_id] = tx
        self._update_status(tx)
        return tx_id

    # ── TX signieren ──────────────────────────────────────────────────────────

    def sign_tx(self, signer: str, tx_id: str) -> dict:
        """
        TX mit Wallet-Adresse `signer` signieren.
        Gibt Status-Dict zurück.
        """
        if signer not in self.owners:
            raise PermissionError(f"{signer} ist kein Owner")
        tx = self._get_active_tx(tx_id)
        if signer in tx.signatures:
            raise ValueError(f"{signer} hat bereits signiert")

        tx.signatures[signer] = self._sign(signer, tx_id, int(time.time()))
        self._update_status(tx)
        return {
            "tx_id":      tx_id,
            "signer":     signer,
            "sig_count":  len(tx.signatures),
            "threshold":  self.threshold,
            "status":     tx.status,
            "ready":      tx.status == TxStatus.READY.value,
        }

    # ── TX ausführen ──────────────────────────────────────────────────────────

    def execute_tx(self, tx_id: str, executor: str) -> dict:
        """
        TX ausführen wenn Threshold erreicht.
        Executor muss Owner sein.
        """
        if executor not in self.owners:
            raise PermissionError(f"{executor} ist kein Owner")
        tx = self._get_active_tx(tx_id)
        if len(tx.signatures) < self.threshold:
            raise ValueError(
                f"Zu wenige Signaturen: {len(tx.signatures)}/{self.threshold}"
            )
        if tx.status == TxStatus.EXPIRED.value:
            raise ValueError("TX ist abgelaufen")

        now           = int(time.time())
        tx.status     = TxStatus.EXECUTED.value
        tx.executed_at = now
        tx.tx_hash    = self._make_tx_hash(tx)

        # Balance-Update (Simulation)
        self._balance -= tx.value

        return {
            "tx_id":      tx_id,
            "status":     "executed",
            "to":         tx.to,
            "value":      tx.value,
            "tx_hash":    tx.tx_hash,
            "executed_at": now,
            "signers":    list(tx.signatures.keys()),
        }

    # ── TX abbrechen ──────────────────────────────────────────────────────────

    def cancel_tx(self, tx_id: str, caller: str) -> bool:
        """TX abbrechen (nur Proposer oder Owner-Mehrheit)."""
        if caller not in self.owners:
            raise PermissionError(f"{caller} ist kein Owner")
        tx = self._get_active_tx(tx_id)
        if caller != tx.proposer:
            raise PermissionError("Nur Proposer darf TX abbrechen")
        tx.status = TxStatus.CANCELLED.value
        return True

    # ── Views ─────────────────────────────────────────────────────────────────

    def get_tx(self, tx_id: str) -> Optional[MultiSigTx]:
        return self._txs.get(tx_id)

    def list_pending(self) -> List[MultiSigTx]:
        """Alle offenen TXs zurückgeben."""
        self._expire_old_txs()
        return [t for t in self._txs.values()
                if t.status in (TxStatus.PENDING.value, TxStatus.READY.value)]

    def get_stats(self) -> dict:
        """Wallet-Statistiken."""
        self._expire_old_txs()
        statuses = [t.status for t in self._txs.values()]
        return {
            "name":      self.name,
            "owners":    len(self.owners),
            "threshold": self.threshold,
            "balance":   self._balance,
            "txs_total": len(self._txs),
            "pending":   statuses.count(TxStatus.PENDING.value),
            "ready":     statuses.count(TxStatus.READY.value),
            "executed":  statuses.count(TxStatus.EXECUTED.value),
            "cancelled": statuses.count(TxStatus.CANCELLED.value),
            "expired":   statuses.count(TxStatus.EXPIRED.value),
        }

    def deposit(self, amount: float):
        """ATC einzahlen (für Tests / Simulation)."""
        if amount <= 0:
            raise ValueError("Betrag muss positiv sein")
        self._balance += amount

    # ── Interne Hilfsmethoden ─────────────────────────────────────────────────

    def _get_active_tx(self, tx_id: str) -> MultiSigTx:
        tx = self._txs.get(tx_id)
        if not tx:
            raise KeyError(f"TX {tx_id} nicht gefunden")
        if tx.status in (TxStatus.EXECUTED.value, TxStatus.CANCELLED.value):
            raise ValueError(f"TX {tx_id} ist bereits {tx.status}")
        return tx

    def _update_status(self, tx: MultiSigTx):
        """Status nach jeder Signatur aktualisieren."""
        if int(time.time()) > tx.expires_at:
            tx.status = TxStatus.EXPIRED.value
        elif len(tx.signatures) >= self.threshold:
            tx.status = TxStatus.READY.value
        else:
            tx.status = TxStatus.PENDING.value

    def _expire_old_txs(self):
        """Abgelaufene TXs markieren."""
        now = int(time.time())
        for tx in self._txs.values():
            if tx.status == TxStatus.PENDING.value and now > tx.expires_at:
                tx.status = TxStatus.EXPIRED.value

    @staticmethod
    def _make_tx_id(proposer: str, to: str, value: float, ts: int) -> str:
        raw = f"{proposer}:{to}:{value}:{ts}".encode()
        return "MSIG-" + hashlib.sha256(raw).hexdigest()[:16].upper()

    @staticmethod
    def _make_tx_hash(tx: MultiSigTx) -> str:
        raw = json.dumps({
            "tx_id": tx.tx_id, "to": tx.to,
            "value": tx.value, "executed_at": tx.executed_at,
        }, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _sign(signer: str, tx_id: str, ts: int) -> str:
        """Simulierte Signatur (echte ECDSA via blockchain/wallet/ecdsa.py)."""
        raw = f"{signer}:{tx_id}:{ts}".encode()
        return hashlib.sha256(raw).hexdigest()[:32]
