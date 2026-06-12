"""
A-TownChain OS — Block Gossip Propagation
Manages block and transaction broadcasting across the P2P network.
Wiki: Kap. 15
"""
import time
import hashlib
import threading
import logging
from typing import Dict, Set, List, Callable, Optional
from dataclasses import dataclass, field

logger = logging.getLogger("blockchain.propagation")

MAX_SEEN      = 50_000
PROPAGATION_K = 8     # forward to K peers
INV_TTL       = 30.0  # seconds before inventory entry expires


@dataclass
class BlockInventory:
    block_hash: str
    height: int
    received_at: float = field(default_factory=time.time)
    propagated_to: Set[str] = field(default_factory=set)

    def is_expired(self) -> bool:
        return (time.time() - self.received_at) > INV_TTL


class BlockGossip:
    """
    Manages block and tx propagation via inventory-based gossip.
    1. Announce: send INV(hash) to peers
    2. Peers request full block via GETBLOCK(hash)
    3. Respond with full block data
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._seen_blocks: Dict[str, BlockInventory] = {}
        self._seen_txs: Set[str] = set()
        self._lock = threading.Lock()
        self._new_block_callbacks: List[Callable] = []
        self._new_tx_callbacks: List[Callable] = []
        threading.Thread(target=self._cleanup_loop, daemon=True).start()
        logger.info(f"BlockGossip initialized node={node_id[:8]}")

    def on_new_block(self, callback: Callable):
        """Register callback for new block announcements."""
        self._new_block_callbacks.append(callback)

    def on_new_tx(self, callback: Callable):
        self._new_tx_callbacks.append(callback)

    def announce_block(self, block: Dict, broadcast_fn: Callable):
        """Announce a new block to the network."""
        block_hash = block.get("hash") or self._compute_hash(block)
        with self._lock:
            if block_hash in self._seen_blocks:
                return  # already propagating
            self._seen_blocks[block_hash] = BlockInventory(
                block_hash=block_hash,
                height=block.get("height", 0)
            )
        inv_msg = {
            "type": "INV",
            "payload": {"kind": "block", "hash": block_hash,
                        "height": block.get("height", 0)},
            "from": self.node_id,
        }
        broadcast_fn(inv_msg)
        logger.info(f"Block announced: {block_hash[:12]} height={block.get('height',0)}")

    def handle_inv(self, msg: Dict, request_fn: Callable):
        """Handle incoming INV message — request block if not seen."""
        payload = msg.get("payload", {})
        kind = payload.get("kind")
        obj_hash = payload.get("hash", "")
        if kind == "block":
            with self._lock:
                if obj_hash in self._seen_blocks:
                    return
            request_fn({"type": "GETBLOCK", "payload": {"hash": obj_hash}})
        elif kind == "tx":
            with self._lock:
                if obj_hash in self._seen_txs:
                    return
            request_fn({"type": "GETTX", "payload": {"hash": obj_hash}})

    def handle_block(self, block: Dict):
        """Process a received full block."""
        block_hash = block.get("hash") or self._compute_hash(block)
        with self._lock:
            if block_hash in self._seen_blocks:
                return
            self._seen_blocks[block_hash] = BlockInventory(
                block_hash=block_hash, height=block.get("height", 0)
            )
        for cb in self._new_block_callbacks:
            try:
                cb(block)
            except Exception as e:
                logger.error(f"Block callback error: {e}")

    def announce_tx(self, tx: Dict, broadcast_fn: Callable):
        """Announce a new transaction."""
        tx_hash = tx.get("hash") or self._compute_hash(tx)
        with self._lock:
            if tx_hash in self._seen_txs:
                return
            if len(self._seen_txs) > MAX_SEEN:
                self._seen_txs.pop()
            self._seen_txs.add(tx_hash)
        broadcast_fn({"type": "INV", "payload": {"kind": "tx", "hash": tx_hash}})

    def handle_tx(self, tx: Dict):
        """Process a received transaction."""
        tx_hash = tx.get("hash") or self._compute_hash(tx)
        with self._lock:
            if tx_hash in self._seen_txs:
                return
            self._seen_txs.add(tx_hash)
        for cb in self._new_tx_callbacks:
            try:
                cb(tx)
            except Exception as e:
                logger.error(f"TX callback error: {e}")

    def _compute_hash(self, data: Dict) -> str:
        import json
        raw = json.dumps(data, sort_keys=True).encode()
        return hashlib.sha256(raw).hexdigest()

    def _cleanup_loop(self):
        while True:
            time.sleep(60)
            with self._lock:
                expired = [h for h, inv in self._seen_blocks.items() if inv.is_expired()]
                for h in expired:
                    del self._seen_blocks[h]
            if expired:
                logger.debug(f"Gossip cleanup: removed {len(expired)} expired block entries")

    def stats(self) -> Dict:
        with self._lock:
            return {
                "seen_blocks": len(self._seen_blocks),
                "seen_txs":    len(self._seen_txs),
                "node_id":     self.node_id[:8],
            }
