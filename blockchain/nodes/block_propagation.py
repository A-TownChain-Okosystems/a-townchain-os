"""
Block Propagation — Issue #15 (ATN-1002)
P2P Block-Broadcasting via Gossip-Protokoll.
Jeder Node sendet neuen Block an K zufällige Peers → exponentielles Spreading.
"""
import json, time, hashlib, threading, logging, socket
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field, asdict

logger = logging.getLogger("atcnet.propagation")

@dataclass
class PropagatedBlock:
    hash:        str
    height:      int
    prev_hash:   str
    timestamp:   float
    data:        dict
    origin:      str   # node_id des Erstellers
    hops:        int = 0

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self)).encode()

    @classmethod
    def from_bytes(cls, raw: bytes) -> "PropagatedBlock":
        return cls(**json.loads(raw.decode()))

class BlockPropagator:
    """
    Gossip-basiertes Block-Broadcasting.
    Protokoll: neu → sende an min(K, len(peers)) Peers
               empfangen → validieren → weiterleiten falls neu
    K = Fanout-Faktor (default: 6)
    """
    FANOUT       = 6
    MAX_SEEN_AGE = 3600   # gesehene Hashes 1h merken
    MAX_HOPS     = 20     # verhindert Endlosschleifen

    def __init__(self, node_id: str, peers: Dict[str, dict]):
        self.node_id    = node_id
        self.peers      = peers          # {node_id: {host, port}}
        self._seen:     Dict[str, float] = {}  # hash → timestamp
        self._lock      = threading.Lock()
        self._callbacks = []             # on_block(block) Handler

    def on_block(self, callback):
        """Callback registrieren, der bei neuem Block aufgerufen wird."""
        self._callbacks.append(callback)

    def _is_seen(self, block_hash: str) -> bool:
        with self._lock:
            self._prune_seen()
            return block_hash in self._seen

    def _mark_seen(self, block_hash: str):
        with self._lock:
            self._seen[block_hash] = time.time()

    def _prune_seen(self):
        cutoff = time.time() - self.MAX_SEEN_AGE
        stale  = [h for h, t in self._seen.items() if t < cutoff]
        for h in stale: del self._seen[h]

    def _select_peers(self, exclude: str = "") -> List[dict]:
        """Wählt bis zu FANOUT zufällige Peers aus (ohne Absender)."""
        import random
        candidates = [p for nid, p in self.peers.items() if nid != exclude]
        return random.sample(candidates, min(self.FANOUT, len(candidates)))

    def _send_udp(self, peer: dict, payload: bytes):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(2.0)
            msg = b"BLOCK:" + payload
            sock.sendto(msg, (peer["host"], peer["port"]))
            sock.close()
        except Exception as e:
            logger.debug(f"[Propagator] Sende-Fehler zu {peer.get('host')}: {e}")

    def broadcast(self, block: PropagatedBlock, from_peer: str = ""):
        """Block an Fanout-Peers weiterleiten (Gossip)."""
        if self._is_seen(block.hash):
            return 0
        if block.hops >= self.MAX_HOPS:
            logger.warning(f"[Propagator] Block {block.hash[:8]} max hops erreicht")
            return 0

        self._mark_seen(block.hash)
        block.hops += 1
        payload = block.to_bytes()
        peers   = self._select_peers(exclude=from_peer)

        threads = []
        for peer in peers:
            t = threading.Thread(target=self._send_udp, args=(peer, payload), daemon=True)
            t.start()
            threads.append(t)
        for t in threads: t.join(timeout=3.0)

        logger.info(f"[Propagator] Block #{block.height} ({block.hash[:8]}) → {len(peers)} Peers (hop {block.hops})")
        return len(peers)

    def receive(self, raw_payload: bytes, from_addr: tuple) -> Optional[PropagatedBlock]:
        """Empfangenen Block verarbeiten."""
        try:
            block = PropagatedBlock.from_bytes(raw_payload)
            if self._is_seen(block.hash):
                return None
            # Callbacks aufrufen
            for cb in self._callbacks:
                try: cb(block)
                except Exception as e: logger.error(f"[Propagator] Callback-Fehler: {e}")
            # Weiterleiten (Gossip)
            threading.Thread(target=self.broadcast, args=(block, block.origin), daemon=True).start()
            return block
        except Exception as e:
            logger.error(f"[Propagator] Parse-Fehler: {e}")
            return None

    def stats(self) -> dict:
        with self._lock:
            return {"seen_blocks": len(self._seen), "peers": len(self.peers)}
