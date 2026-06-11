# blockchain/consensus/hybrid_consensus.py
# A-TownChain Hybrid Consensus: SHA-256 PoW + PoS + PoH
# FIX #8/#9: poh_entry ist ein @dataclass Objekt — Attribut-Zugriff via .hash / .sequence
# FIX #10: validate_chain() prüft jetzt auch PoH-Sequenz

import hashlib, time, json
from blockchain.consensus.pow import ProofOfWork
from blockchain.consensus.pos import ProofOfStake
from blockchain.consensus.poh import ProofOfHistory

class HybridConsensus:
    """
    Kombinierter Konsens-Mechanismus:
      PoH → verifizierbarer Zeitbeweis (SHA-3_256 VDF)
      PoW → Miner findet Hash (SHA-256, difficulty-adjusting)
      PoS → Validator bestätigt Block (stake-weighted)
    Reihenfolge: PoH → PoW → PoS
    """

    def __init__(self, difficulty: int = 3):
        self.pow    = ProofOfWork(difficulty)
        self.pos    = ProofOfStake()
        self.poh    = ProofOfHistory()
        self.blocks = []
        self.height = 0

    def create_block(self, transactions: list, miner: str) -> dict:
        """Erstellt einen neuen Block durch den hybriden Konsens."""

        # ── Schritt 1: PoH Tick ─────────────────────────────────────
        poh_entry = self.poh.tick(json.dumps(transactions).encode())
        # FIX #8/#9: poh_entry ist PoHEntry @dataclass → .hash, .sequence (nicht [])
        poh_hash_val = poh_entry.hash
        poh_seq_val  = poh_entry.seq

        # ── Schritt 2: Block-Daten zusammenstellen ──────────────────
        prev_hash = self.blocks[-1]["hash"] if self.blocks else "0" * 64
        block_data = {
            "height":       self.height + 1,
            "prev_hash":    prev_hash,
            "poh_hash":     poh_hash_val,
            "poh_sequence": poh_seq_val,
            "transactions": transactions,
            "miner":        miner,
            "timestamp":    int(time.time())
        }

        # ── Schritt 3: PoW Mining ────────────────────────────────────
        pow_result = self.pow.mine_block(block_data)
        block_data["hash"]       = pow_result["hash"]
        block_data["nonce"]      = pow_result["nonce"]
        block_data["difficulty"] = pow_result["difficulty"]

        # ── Schritt 4: PoS Validator-Bestätigung ─────────────────────
        validator = self.pos.select_validator(seed=pow_result["hash"])
        block_data["validator"] = validator or "genesis"
        block_data["reward"]    = self.pow.get_block_reward(self.height + 1)

        # ── Finalisierung ─────────────────────────────────────────────
        self.blocks.append(block_data)
        self.height += 1
        return block_data

    def get_chain_info(self) -> dict:
        return {
            "height":     self.height,
            "algorithm":  "SHA-3_256 PoH + SHA-256 PoW + PoS",
            "difficulty": self.pow.difficulty,
            "pow":        {"difficulty": self.pow.difficulty, "target": self.pow.target},
            "pos":        self.pos.get_stats(),
            "poh":        self.poh.get_state(),
            "last_block": self.blocks[-1]["hash"][:16] + "..." if self.blocks else None
        }

    def validate_chain(self) -> bool:
        """
        Verifiziert die gesamte Chain.
        FIX #10: Prüft jetzt PoH-Sequenz-Monotonie zusätzlich zu prev_hash + PoW.
        """
        last_poh_seq = 0
        for i in range(1, len(self.blocks)):
            b    = self.blocks[i]
            prev = self.blocks[i-1]
            # 1. Hash-Verkettung
            if b["prev_hash"] != prev["hash"]:
                return False
            # 2. PoW-Validierung
            block_for_pow = {k: v for k, v in b.items() if k not in ("hash","nonce")}
            if not self.pow.validate_block(block_for_pow, b["nonce"], b["hash"]):
                return False
            # 3. FIX #10: PoH-Sequenz muss strikt monoton steigen
            if b.get("poh_sequence", 0) <= prev.get("poh_sequence", -1):
                return False
        return True
