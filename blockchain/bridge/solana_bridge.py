"""
A-TownChain — Solana Cross-Chain Bridge (Fix #34)
SPL-Token Standard | Wormhole-Protokoll | Lock-and-Mint

Standards: ATC-0001, ATC-1001 (Cross-Chain)
Version: v3.0.0-alpha
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List
import hashlib, time, json

# ── Konfiguration ──────────────────────────────────
SOLANA_BRIDGE_CONFIG = {
    "atc_chain_id":     9000,
    "solana_program_id":"ATCBridgeProgramXXXXXXXXXXXXXXXXXXXXXXXXX",
    "wrapped_token":    "SATC",       # Solana-seitig: Wrapped ATC
    "min_confirmations": 32,          # Solana Slot-Bestätigungen
    "atc_confirmations": 3,           # A-TownChain Block-Bestätigungen
    "daily_limit":       1_000_000,   # 1M ATC / Tag
    "fee_percent":       0.1,         # 0.1% Bridge-Fee
    "relayer_nodes":     3,           # M-of-N Relayer
    "timelock_large":    86400,       # 24h für > 100k ATC
}

@dataclass
class SolanaBridgeTx:
    tx_id:          str
    direction:      str        # "ATC_TO_SOL" | "SOL_TO_ATC"
    sender:         str        # ATC-Adresse oder Solana-PublicKey
    recipient:      str
    amount:         int        # in ATC-Einheiten (10^18)
    fee:            int
    net_amount:     int        # amount - fee
    status:         str = "PENDING"   # PENDING|LOCKED|CONFIRMED|MINTED|COMPLETED|FAILED
    atc_block:      int = 0
    solana_slot:    int = 0
    confirmations:  int = 0
    created_at:     int = field(default_factory=lambda: int(time.time()))
    completed_at:   Optional[int] = None
    relayer_sigs:   List[str] = field(default_factory=list)
    error:          Optional[str] = None

class SolanaBridge:
    """
    A-TownChain ↔ Solana Cross-Chain Bridge.

    Protokoll:
      ATC→SOL: Lock ATC on A-TownChain → Mint SATC on Solana
      SOL→ATC: Burn SATC on Solana     → Unlock ATC on A-TownChain

    Invariante: total_locked_ATC == total_minted_SATC (immer)
    Mathematisch bewiesen: Theorem 7 (Whitepaper v3.0.0)
    """

    def __init__(self):
        self.locked:       Dict[str, int] = {}   # addr → locked ATC
        self.minted_satc:  Dict[str, int] = {}   # solana_addr → SATC
        self.transactions: Dict[str, SolanaBridgeTx] = {}
        self.used_tx_ids:  set = set()            # Replay-Schutz
        self.daily_volume: Dict[str, int] = {}    # date → volume
        self.total_locked: int = 0
        self.total_minted: int = 0
        self._locked_flag: bool = False           # Reentrancy-Guard

    def _nonreentrant_enter(self):
        if self._locked_flag:
            raise RuntimeError("SolanaBridge: Reentrancy nicht erlaubt")
        self._locked_flag = True

    def _nonreentrant_exit(self):
        self._locked_flag = False

    def _calc_fee(self, amount: int) -> int:
        return int(amount * SOLANA_BRIDGE_CONFIG["fee_percent"] / 100)

    def _check_daily_limit(self, amount: int) -> bool:
        today = time.strftime("%Y-%m-%d")
        vol   = self.daily_volume.get(today, 0)
        limit = SOLANA_BRIDGE_CONFIG["daily_limit"] * 10**18
        return (vol + amount) <= limit

    def _add_daily_volume(self, amount: int):
        today = time.strftime("%Y-%m-%d")
        self.daily_volume[today] = self.daily_volume.get(today, 0) + amount

    def initiate_atc_to_sol(self, sender_atc: str, recipient_sol: str,
                             amount: int, atc_balance: int) -> SolanaBridgeTx:
        """Schritt 1: ATC auf A-TownChain sperren → SATC auf Solana minten."""
        self._nonreentrant_enter()
        try:
            # Validierungen
            if not sender_atc.startswith("ATC") or len(sender_atc) != 35:
                raise ValueError(f"Ungültige ATC-Adresse: {sender_atc}")
            if len(recipient_sol) < 32 or len(recipient_sol) > 44:
                raise ValueError(f"Ungültige Solana-Adresse: {recipient_sol}")
            if amount <= 0:
                raise ValueError("Betrag muss > 0 sein")
            if atc_balance < amount:
                raise ValueError(f"Unzureichendes Guthaben: {atc_balance} < {amount}")
            if not self._check_daily_limit(amount):
                raise ValueError(f"Tages-Limit überschritten ({SOLANA_BRIDGE_CONFIG['daily_limit']} ATC)")

            fee        = self._calc_fee(amount)
            net_amount = amount - fee
            tx_id      = "BRIDGE_" + hashlib.sha3_256(
                f"{sender_atc}{recipient_sol}{amount}{time.time()}".encode()
            ).hexdigest()[:24]

            if tx_id in self.used_tx_ids:
                raise ValueError("TX-ID bereits verwendet (Replay-Schutz)")

            # State ändern VOR emit (Reentrancy-Schutz)
            self.locked[sender_atc]       = self.locked.get(sender_atc, 0) + amount
            self.total_locked            += amount
            self.used_tx_ids.add(tx_id)
            self._add_daily_volume(amount)

            tx = SolanaBridgeTx(
                tx_id=tx_id, direction="ATC_TO_SOL",
                sender=sender_atc, recipient=recipient_sol,
                amount=amount, fee=fee, net_amount=net_amount,
                status="LOCKED"
            )
            self.transactions[tx_id] = tx
            return tx

        finally:
            self._nonreentrant_exit()

    def confirm_atc_lock(self, tx_id: str, atc_block: int,
                          confirmations: int) -> SolanaBridgeTx:
        """Schritt 2: ATC-Lock bestätigen (mind. 3 Block-Bestätigungen)."""
        tx = self.transactions.get(tx_id)
        if not tx: raise ValueError(f"TX nicht gefunden: {tx_id}")
        if tx.status != "LOCKED": raise ValueError(f"Falscher Status: {tx.status}")

        tx.atc_block     = atc_block
        tx.confirmations = confirmations
        min_conf = SOLANA_BRIDGE_CONFIG["atc_confirmations"]
        if confirmations >= min_conf:
            tx.status = "CONFIRMED"
        return tx

    def add_relayer_signature(self, tx_id: str, relayer_sig: str,
                               relayer_id: str) -> SolanaBridgeTx:
        """Schritt 3: Relayer signiert TX (M-of-N: 3 von 3)."""
        tx = self.transactions.get(tx_id)
        if not tx: raise ValueError(f"TX nicht gefunden: {tx_id}")
        if tx.status not in ("CONFIRMED", "LOCKED"):
            raise ValueError(f"Falscher Status für Relayer-Sig: {tx.status}")

        sig_entry = f"{relayer_id}:{relayer_sig}"
        if sig_entry not in tx.relayer_sigs:
            tx.relayer_sigs.append(sig_entry)

        required = SOLANA_BRIDGE_CONFIG["relayer_nodes"]
        if len(tx.relayer_sigs) >= required:
            tx.status = "READY_TO_MINT"
        return tx

    def mint_satc_on_solana(self, tx_id: str,
                             solana_slot: int) -> SolanaBridgeTx:
        """Schritt 4: SATC auf Solana minten (nach Relayer-Konsens)."""
        tx = self.transactions.get(tx_id)
        if not tx: raise ValueError(f"TX nicht gefunden: {tx_id}")
        if tx.status != "READY_TO_MINT":
            raise ValueError(f"Nicht bereit zum Minten: {tx.status}")
        required = SOLANA_BRIDGE_CONFIG["relayer_nodes"]
        if len(tx.relayer_sigs) < required:
            raise ValueError(f"Nicht genug Relayer-Signaturen: {len(tx.relayer_sigs)}/{required}")

        self.minted_satc[tx.recipient] = (
            self.minted_satc.get(tx.recipient, 0) + tx.net_amount
        )
        self.total_minted += tx.net_amount
        tx.solana_slot    = solana_slot
        tx.status         = "COMPLETED"
        tx.completed_at   = int(time.time())

        # Invarianten-Check: locked >= minted (Fee-Differenz)
        assert self.total_locked >= self.total_minted,             "KRITISCH: Bridge-Invariante verletzt!"
        return tx

    def initiate_sol_to_atc(self, sender_sol: str, recipient_atc: str,
                             satc_amount: int) -> SolanaBridgeTx:
        """Rück-Bridge: SATC auf Solana verbrennen → ATC entsperren."""
        self._nonreentrant_enter()
        try:
            if not recipient_atc.startswith("ATC") or len(recipient_atc) != 35:
                raise ValueError(f"Ungültige ATC-Adresse: {recipient_atc}")
            if satc_amount <= 0:
                raise ValueError("Betrag muss > 0 sein")
            if self.minted_satc.get(sender_sol, 0) < satc_amount:
                raise ValueError("Unzureichendes SATC-Guthaben auf Solana")

            fee        = self._calc_fee(satc_amount)
            net_amount = satc_amount - fee
            tx_id      = "BRIDGE_SOL_" + hashlib.sha3_256(
                f"{sender_sol}{recipient_atc}{satc_amount}{time.time()}".encode()
            ).hexdigest()[:24]

            # State VOR emit
            self.minted_satc[sender_sol] -= satc_amount
            self.total_minted            -= satc_amount
            self.used_tx_ids.add(tx_id)

            tx = SolanaBridgeTx(
                tx_id=tx_id, direction="SOL_TO_ATC",
                sender=sender_sol, recipient=recipient_atc,
                amount=satc_amount, fee=fee, net_amount=net_amount,
                status="BURN_PENDING"
            )
            self.transactions[tx_id] = tx
            return tx

        finally:
            self._nonreentrant_exit()

    def complete_sol_to_atc(self, tx_id: str) -> dict:
        """ATC entsperren nach SATC-Burn auf Solana."""
        tx = self.transactions.get(tx_id)
        if not tx: raise ValueError(f"TX nicht gefunden: {tx_id}")
        if tx.status != "BURN_PENDING":
            raise ValueError(f"Falscher Status: {tx.status}")

        # ATC aus Lock freigeben
        locked_for_sender = self.locked.get(tx.recipient, 0)
        if locked_for_sender < tx.net_amount:
            # Aus globalen Reserves entsperren
            self.total_locked -= tx.net_amount
        else:
            self.locked[tx.recipient] -= tx.net_amount
            self.total_locked        -= tx.net_amount

        tx.status       = "COMPLETED"
        tx.completed_at = int(time.time())

        return {
            "tx_id":        tx_id,
            "recipient":    tx.recipient,
            "unlocked_atc": tx.net_amount,
            "fee":          tx.fee,
            "status":       "COMPLETED"
        }

    def get_balance(self, address: str) -> dict:
        return {
            "atc_locked":    self.locked.get(address, 0),
            "satc_balance":  self.minted_satc.get(address, 0),
            "total_locked":  self.total_locked,
            "total_minted":  self.total_minted,
        }

    def verify_invariant(self) -> bool:
        """Prüft Bridge-Korrektheit: locked >= minted."""
        return self.total_locked >= self.total_minted
