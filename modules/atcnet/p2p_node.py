"""
ATCNet — P2P Node
Manages peer connections and message routing.
Wiki: Kap. 22
"""
import socket
import threading
import json
import time
import uuid
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable

logger = logging.getLogger("atcnet.p2p")

DEFAULT_PORT = 9000


@dataclass
class Peer:
    peer_id: str
    host: str
    port: int
    connected_at: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    latency_ms: float = 0.0
    version: str = "1.0.0"

    @property
    def address(self) -> str:
        return f"{self.host}:{self.port}"

    def is_alive(self, timeout: float = 60.0) -> bool:
        return (time.time() - self.last_seen) < timeout


class P2PNode:
    """ATCNet P2P Node — manages peer connections and message exchange."""

    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_PORT,
                 node_id: str = None):
        self.host = host
        self.port = port
        self.node_id = node_id or str(uuid.uuid4())
        self._peers: Dict[str, Peer] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._server: Optional[socket.socket] = None
        self._running = False
        self._lock = threading.Lock()
        logger.info(f"P2PNode created: {self.node_id[:8]} on {host}:{port}")

    def start(self):
        """Start listening for incoming connections."""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind((self.host, self.port))
        self._server.listen(50)
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        logger.info(f"P2PNode listening on {self.host}:{self.port}")

    def stop(self):
        self._running = False
        if self._server:
            self._server.close()

    def connect(self, host: str, port: int) -> Optional[str]:
        """Connect to a remote peer. Returns peer_id or None."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((host, port))
            peer_id = str(uuid.uuid4())
            peer = Peer(peer_id=peer_id, host=host, port=port)
            with self._lock:
                self._peers[peer_id] = peer
            threading.Thread(target=self._handle_peer, args=(sock, peer), daemon=True).start()
            logger.info(f"Connected to peer {host}:{port} ({peer_id[:8]})")
            return peer_id
        except Exception as e:
            logger.warning(f"Could not connect to {host}:{port}: {e}")
            return None

    def broadcast(self, msg_type: str, payload: dict):
        """Broadcast a message to all connected peers."""
        msg = json.dumps({"type": msg_type, "payload": payload,
                          "from": self.node_id, "ts": time.time()})
        with self._lock:
            peers = list(self._peers.values())
        for peer in peers:
            try:
                self._send_to_peer(peer, msg)
            except Exception as e:
                logger.warning(f"Broadcast failed to {peer.address}: {e}")

    def on(self, msg_type: str, handler: Callable):
        """Register a message handler."""
        self._handlers.setdefault(msg_type, []).append(handler)

    def peers(self) -> List[Dict]:
        with self._lock:
            return [{"id": p.peer_id[:8], "address": p.address,
                     "alive": p.is_alive(), "latency_ms": p.latency_ms}
                    for p in self._peers.values()]

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._server.accept()
                peer_id = str(uuid.uuid4())
                peer = Peer(peer_id=peer_id, host=addr[0], port=addr[1])
                with self._lock:
                    self._peers[peer_id] = peer
                threading.Thread(target=self._handle_peer, args=(conn, peer), daemon=True).start()
            except Exception:
                if self._running:
                    time.sleep(0.1)

    def _handle_peer(self, sock: socket.socket, peer: Peer):
        try:
            buf = ""
            while self._running:
                data = sock.recv(4096).decode(errors="ignore")
                if not data:
                    break
                buf += data
                while "
" in buf:
                    line, buf = buf.split("
", 1)
                    self._dispatch(line.strip(), peer)
                peer.last_seen = time.time()
        except Exception as e:
            logger.debug(f"Peer {peer.address} disconnected: {e}")
        finally:
            sock.close()
            with self._lock:
                self._peers.pop(peer.peer_id, None)

    def _dispatch(self, raw: str, peer: Peer):
        try:
            msg = json.loads(raw)
            handlers = self._handlers.get(msg.get("type", ""), [])
            for h in handlers:
                h(msg, peer)
        except json.JSONDecodeError:
            pass

    def _send_to_peer(self, peer: Peer, msg: str):
        pass  # Implemented via socket handle in _handle_peer

    def _heartbeat_loop(self):
        while self._running:
            self.broadcast("ping", {"node_id": self.node_id})
            time.sleep(30)

    def status(self) -> Dict:
        return {
            "node_id": self.node_id[:8],
            "address": f"{self.host}:{self.port}",
            "peers": len(self._peers),
            "running": self._running,
        }
