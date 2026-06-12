"""
ATCNet — Gossip Protocol
Block and transaction propagation via gossip.
Wiki: Kap. 22
"""
import time
import threading
import hashlib
import logging
from typing import Dict, Set, Callable, Any
from dataclasses import dataclass, field

logger = logging.getLogger("atcnet.gossip")

MAX_TTL    = 10       # max hops
FANOUT     = 5        # broadcast to N peers
SEEN_LIMIT = 10000    # max cached message IDs


@dataclass
class GossipMessage:
    msg_id: str
    msg_type: str   # "block", "tx", "peer_announce"
    payload: Dict
    ttl: int = MAX_TTL
    origin: str = ""
    timestamp: float = field(default_factory=time.time)


class GossipProtocol:
    """
    Epidemic gossip protocol for block and tx propagation.
    Each message is forwarded to FANOUT peers until TTL=0.
    Seen messages are deduplicated via a rolling set.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self._seen: Set[str] = set()
        self._seen_order: list = []
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        logger.info(f"GossipProtocol init node={node_id[:8]}")

    def _msg_id(self, msg_type: str, payload: Dict) -> str:
        raw = f"{msg_type}:{sorted(payload.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _mark_seen(self, msg_id: str):
        with self._lock:
            if msg_id not in self._seen:
                self._seen.add(msg_id)
                self._seen_order.append(msg_id)
                if len(self._seen_order) > SEEN_LIMIT:
                    old = self._seen_order.pop(0)
                    self._seen.discard(old)

    def _is_seen(self, msg_id: str) -> bool:
        with self._lock:
            return msg_id in self._seen

    def on(self, msg_type: str, handler: Callable):
        """Register handler for a message type."""
        self._handlers[msg_type] = handler

    def receive(self, msg: GossipMessage, forward_fn: Callable = None):
        """Process an incoming gossip message."""
        if self._is_seen(msg.msg_id):
            return  # already processed
        self._mark_seen(msg.msg_id)

        # Dispatch to handler
        handler = self._handlers.get(msg.msg_type)
        if handler:
            try:
                handler(msg.payload)
            except Exception as e:
                logger.error(f"Gossip handler error ({msg.msg_type}): {e}")

        # Forward if TTL > 0
        if msg.ttl > 0 and forward_fn:
            forwarded = GossipMessage(
                msg_id=msg.msg_id,
                msg_type=msg.msg_type,
                payload=msg.payload,
                ttl=msg.ttl - 1,
                origin=self.node_id,
            )
            try:
                forward_fn(forwarded)
            except Exception as e:
                logger.warning(f"Gossip forward failed: {e}")

    def broadcast_block(self, block_data: Dict, forward_fn: Callable = None):
        """Gossip a new block to the network."""
        msg_id = self._msg_id("block", {"hash": block_data.get("hash","")})
        msg = GossipMessage(msg_id=msg_id, msg_type="block",
                            payload=block_data, origin=self.node_id)
        self._mark_seen(msg_id)
        if forward_fn:
            forward_fn(msg)
        logger.info(f"Gossip: broadcast block {block_data.get('hash','?')[:12]}")

    def broadcast_tx(self, tx_data: Dict, forward_fn: Callable = None):
        """Gossip a new transaction."""
        msg_id = self._msg_id("tx", {"hash": tx_data.get("hash","")})
        msg = GossipMessage(msg_id=msg_id, msg_type="tx",
                            payload=tx_data, origin=self.node_id)
        self._mark_seen(msg_id)
        if forward_fn:
            forward_fn(msg)

    def stats(self) -> Dict:
        with self._lock:
            return {"seen_messages": len(self._seen), "node_id": self.node_id[:8]}
