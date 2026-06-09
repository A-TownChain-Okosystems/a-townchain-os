"""
Longest-Chain-Rule & Fork-Auflösung — Issue #17 (ATC-1004)
Bei konkurrierenden Chains gewinnt die schwerste/längste.
Implementiert Nakamoto-Konsens für PoW + PoH-gewichtete Variante.
"""
import hashlib, time, logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger("atcchain.fork")

@dataclass
class ChainBlock:
    height:    int
    hash:      str
    prev_hash: str
    timestamp: float
    difficulty: int = 1
    work:       int = 0      # kumulativer Work (Summe der Difficulties)
    poh_ticks:  int = 0      # PoH-Ticks seit Genesis

    def __hash__(self): return hash(self.hash)

@dataclass
class Fork:
    tip:    ChainBlock
    blocks: List[ChainBlock] = field(default_factory=list)

    @property
    def height(self) -> int:
        return self.tip.height

    @property
    def total_work(self) -> int:
        return sum(b.work for b in self.blocks)

    @property
    def total_poh(self) -> int:
        return self.tip.poh_ticks

class ForkResolver:
    """
    Löst Chain-Forks auf.
    Auswahl-Priorität:
      1. Längste Chain (höchste Höhe)
      2. Bei Gleichstand: meister kumulativer PoW-Work
      3. Bei Gleichstand: meiste PoH-Ticks
      4. Bei Gleichstand: ältester Tip-Timestamp (früher = bevorzugt)
    """

    def __init__(self, genesis_hash: str = "0"*64):
        self.genesis_hash = genesis_hash
        self._chains: Dict[str, Fork] = {}   # tip_hash → Fork

    def add_block(self, block: ChainBlock):
        """Neuen Block ins Fork-Register eintragen."""
        # Gibt es einen Fork auf dem Prev-Block?
        parent_fork = self._chains.pop(block.prev_hash, None)
        if parent_fork:
            parent_fork.blocks.append(block)
            parent_fork.tip = block
            self._chains[block.hash] = parent_fork
        else:
            # Neuer Fork-Zweig
            self._chains[block.hash] = Fork(tip=block, blocks=[block])

    def canonical_chain(self) -> Optional[Fork]:
        """Gibt die kanonische (beste) Chain zurück."""
        if not self._chains:
            return None
        return max(
            self._chains.values(),
            key=lambda f: (f.height, f.total_work, f.total_poh, -f.tip.timestamp)
        )

    def detect_fork(self) -> bool:
        """True wenn mehr als ein aktiver Fork-Zweig existiert."""
        return len(self._chains) > 1

    def resolve(self) -> Tuple[Optional[Fork], List[Fork]]:
        """
        Löst Fork auf.
        Returns: (winner, orphaned_forks)
        """
        if not self._chains:
            return None, []

        winner  = self.canonical_chain()
        orphans = [f for h, f in self._chains.items() if f is not winner]

        if orphans:
            logger.info(
                f"[Fork] Auflösung: winner Höhe={winner.height} "
                f"work={winner.total_work} | {len(orphans)} verwaiste Forks"
            )
            for o in orphans:
                logger.debug(f"  orphan: Höhe={o.height} tip={o.tip.hash[:8]}")

        # Nur noch Winner behalten
        self._chains = {winner.tip.hash: winner}
        return winner, orphans

    def rollback_depth(self, fork_a: Fork, fork_b: Fork) -> int:
        """Berechnet wie tief ein Rollback nötig wäre (gemeinsamer Ancestor)."""
        hashes_a = {b.hash for b in fork_a.blocks}
        for i, block in enumerate(reversed(fork_b.blocks)):
            if block.hash in hashes_a or block.prev_hash in hashes_a:
                return i
        return len(fork_b.blocks)

    def stats(self) -> dict:
        canonical = self.canonical_chain()
        return {
            "active_forks":  len(self._chains),
            "canonical_height": canonical.height if canonical else 0,
            "canonical_work": canonical.total_work if canonical else 0,
        }
