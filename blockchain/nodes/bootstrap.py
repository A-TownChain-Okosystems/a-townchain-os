"""
Bootstrap Node — ATN-1000 Standard (Sprint 2.2 Fix)
Permanenter Discovery-Node, der neue Peers ins Netzwerk einführt.
Löst GitHub Issue #14.
"""
import socket, threading, json, time, logging, signal, sys
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Set
from pathlib import Path

logger = logging.getLogger("atc.bootstrap")

BOOTSTRAP_PORT    = 4001
BOOTSTRAP_VERSION = "2.0.0"
PEER_TTL          = 3600   # 1h inaktiv → entfernen
MAX_PEERS         = 1000
HEARTBEAT_INTERVAL = 30    # Sekunden

@dataclass
class Peer:
    node_id: str
    host: str
    port: int
    last_seen: float = field(default_factory=time.time)
    version: str = BOOTSTRAP_VERSION
    capabilities: List[str] = field(default_factory=list)

    def is_alive(self) -> bool:
        return (time.time() - self.last_seen) < PEER_TTL

    def to_dict(self): return asdict(self)

class BootstrapNode:
    """
    Permanenter Bootstrap-Node für ATCNet.
    - Neue Nodes melden sich an (ANNOUNCE)
    - Bootstrap antwortet mit Peer-Liste (PEER_LIST)
    - Heartbeat entfernt tote Peers
    - Persistiert Peer-Liste auf Disk
    """

    def __init__(self, host="0.0.0.0", port=BOOTSTRAP_PORT,
                 data_dir="/var/atc/bootstrap"):
        self.host       = host
        self.port       = port
        self.data_dir   = Path(data_dir)
        self.peers: Dict[str, Peer] = {}
        self._lock      = threading.Lock()
        self._running   = False
        self.sock       = None
        self._load_peers()

    # ── Persistenz ────────────────────────────────────────
    def _peers_file(self) -> Path:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "peers.json"

    def _load_peers(self):
        p = self._peers_file()
        if p.exists():
            try:
                data = json.loads(p.read_text())
                for d in data:
                    peer = Peer(**d)
                    if peer.is_alive():
                        self.peers[peer.node_id] = peer
                logger.info(f"[Bootstrap] {len(self.peers)} Peers geladen")
            except Exception as e:
                logger.warning(f"[Bootstrap] Peer-Datei fehlerhaft: {e}")

    def _save_peers(self):
        try:
            data = [p.to_dict() for p in self.peers.values()]
            self._peers_file().write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"[Bootstrap] Speichern fehlgeschlagen: {e}")

    # ── Nachrichten ───────────────────────────────────────
    def _handle_msg(self, raw: bytes, addr) -> bytes:
        try:
            msg = json.loads(raw.decode())
        except Exception:
            return json.dumps({"type": "ERROR", "msg": "Invalid JSON"}).encode()

        msg_type = msg.get("type", "")

        if msg_type == "ANNOUNCE":
            return self._handle_announce(msg, addr)
        elif msg_type == "PING":
            return self._handle_ping(msg, addr)
        elif msg_type == "GET_PEERS":
            return self._handle_get_peers(msg)
        elif msg_type == "LEAVE":
            return self._handle_leave(msg)
        else:
            return json.dumps({"type": "ERROR", "msg": f"Unknown: {msg_type}"}).encode()

    def _handle_announce(self, msg: dict, addr) -> bytes:
        node_id = msg.get("node_id", "")
        host    = msg.get("host") or addr[0]
        port    = msg.get("port", BOOTSTRAP_PORT)
        caps    = msg.get("capabilities", [])
        with self._lock:
            peer = Peer(node_id=node_id, host=host, port=port,
                        last_seen=time.time(), capabilities=caps)
            self.peers[node_id] = peer
            active = [p.to_dict() for p in self.peers.values()
                      if p.is_alive() and p.node_id != node_id][:50]
        logger.info(f"[Bootstrap] ANNOUNCE {node_id[:12]}… von {host}:{port}")
        return json.dumps({"type": "PEER_LIST", "peers": active,
                           "bootstrap_id": "atc-bootstrap-v2"}).encode()

    def _handle_ping(self, msg: dict, addr) -> bytes:
        node_id = msg.get("node_id", "")
        with self._lock:
            if node_id in self.peers:
                self.peers[node_id].last_seen = time.time()
        return json.dumps({"type": "PONG", "ts": time.time()}).encode()

    def _handle_get_peers(self, msg: dict) -> bytes:
        limit = min(msg.get("limit", 50), 100)
        with self._lock:
            peers = [p.to_dict() for p in self.peers.values()
                     if p.is_alive()][:limit]
        return json.dumps({"type": "PEER_LIST", "peers": peers}).encode()

    def _handle_leave(self, msg: dict) -> bytes:
        node_id = msg.get("node_id", "")
        with self._lock:
            self.peers.pop(node_id, None)
        return json.dumps({"type": "ACK"}).encode()

    # ── Heartbeat ─────────────────────────────────────────
    def _heartbeat(self):
        while self._running:
            time.sleep(HEARTBEAT_INTERVAL)
            with self._lock:
                before = len(self.peers)
                self.peers = {k: v for k, v in self.peers.items() if v.is_alive()}
                removed = before - len(self.peers)
                if removed:
                    logger.info(f"[Bootstrap] Heartbeat: {removed} tote Peers entfernt")
            self._save_peers()

    # ── Server ────────────────────────────────────────────
    def start(self):
        self._running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        logger.info(f"[Bootstrap] Listening on {self.host}:{self.port}")

        threading.Thread(target=self._heartbeat, daemon=True).start()

        def _recv():
            while self._running:
                try:
                    data, addr = self.sock.recvfrom(65535)
                    response = self._handle_msg(data, addr)
                    self.sock.sendto(response, addr)
                except OSError:
                    break
                except Exception as e:
                    logger.error(f"[Bootstrap] Fehler: {e}")

        threading.Thread(target=_recv, daemon=False).start()

    def stop(self):
        self._running = False
        if self.sock:
            self.sock.close()
        self._save_peers()
        logger.info("[Bootstrap] Gestoppt")

    def stats(self) -> dict:
        with self._lock:
            return {
                "total": len(self.peers),
                "alive": sum(1 for p in self.peers.values() if p.is_alive()),
                "port":  self.port,
            }

# ── CLI Entry Point ──────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(message)s")
    node = BootstrapNode()
    node.start()
    def _stop(sig, frame):
        node.stop(); sys.exit(0)
    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)
    print(f"[Bootstrap] ATCNet Bootstrap Node v{BOOTSTRAP_VERSION} läuft")
    while True: time.sleep(1)

    def _handle_message(self, data: bytes, addr) -> bytes:
        """Verarbeitet eingehende UDP-Nachricht und gibt Antwort zurück."""
        import json, time
        try:
            msg = json.loads(data.decode())
            msg_type = msg.get("type","")
            if msg_type == "ANNOUNCE":
                node_id = msg["node_id"]
                self.peers[node_id] = {
                    "node_id": node_id, "host": msg.get("host", addr[0]),
                    "port": msg.get("port", addr[1]),
                    "capabilities": msg.get("capabilities", []),
                    "last_seen": time.time(),
                }
                peers_list = [v for k,v in list(self.peers.items())[:50] if k != node_id]
                return json.dumps({"type": "PEER_LIST", "peers": peers_list}).encode()
            elif msg_type == "PING":
                node_id = msg.get("node_id","?")
                if node_id in self.peers:
                    self.peers[node_id]["last_seen"] = time.time()
                return json.dumps({"type": "PONG", "ts": time.time()}).encode()
            elif msg_type == "GET_PEERS":
                limit = min(int(msg.get("limit", 50)), 100)
                peers_list = list(self.peers.values())[:limit]
                return json.dumps({"type": "PEER_LIST", "peers": peers_list}).encode()
            else:
                return json.dumps({"type": "ERROR", "message": f"Unknown type: {msg_type}"}).encode()
        except Exception as e:
            return json.dumps({"type": "ERROR", "message": str(e)}).encode()

    def _cleanup_stale_peers(self, max_age: float = 1800):
        """Entfernt Peers die länger als max_age Sekunden inaktiv waren."""
        import time
        cutoff = time.time() - max_age
        stale = [k for k, v in self.peers.items() if v.get("last_seen", 0) < cutoff]
        for k in stale:
            del self.peers[k]
        return len(stale)
