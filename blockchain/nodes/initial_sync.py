"""
Initial Sync — Issue #16 (ATN-1003)
Neue Nodes laden die komplette Chain von einem Sync-Peer.
Protokoll: REQUEST_CHAIN_INFO → REQUEST_BLOCKS(from, to) → APPLY
"""
import json, socket, time, logging, threading
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger("atcnet.sync")

@dataclass
class SyncBlock:
    height:    int
    hash:      str
    prev_hash: str
    timestamp: float
    data:      dict

@dataclass
class SyncPeer:
    node_id:   str
    host:      str
    port:      int
    height:    int = 0    # letzte bekannte Chain-Höhe
    latency_ms: float = 0.0

class InitialSyncer:
    """
    Chain-Synchronisation für neue/zurückgefallene Nodes.
    1. CHAIN_INFO: eigene Höhe an Peers melden, ihre Höhe abfragen
    2. Best Peer wählen (höchste Chain, niedrigste Latenz)
    3. Blocks in Batches laden (BATCH_SIZE=50)
    4. Jeden Block validieren und anwenden
    """
    BATCH_SIZE   = 50
    TIMEOUT      = 10.0
    MAX_RETRIES  = 3

    def __init__(self, node_id: str, current_height: int, peers: List[SyncPeer]):
        self.node_id        = node_id
        self.current_height = current_height
        self.peers          = peers
        self._on_block:  Optional[Callable] = None
        self._on_done:   Optional[Callable] = None
        self._running       = False
        self._progress      = 0

    def on_block(self, cb: Callable): self._on_block = cb
    def on_done(self,  cb: Callable): self._on_done  = cb

    def _query_peer_height(self, peer: SyncPeer) -> int:
        """Fragt Peer nach seiner aktuellen Chain-Höhe."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.TIMEOUT)
            t0 = time.time()
            msg = json.dumps({"type": "CHAIN_INFO", "node_id": self.node_id,
                               "height": self.current_height}).encode()
            sock.sendto(msg, (peer.host, peer.port))
            data, _ = sock.recvfrom(65535)
            peer.latency_ms = (time.time() - t0) * 1000
            resp = json.loads(data.decode())
            return int(resp.get("height", 0))
        except Exception as e:
            logger.debug(f"[Sync] {peer.host}: {e}")
            return 0
        finally:
            sock.close()

    def _fetch_blocks(self, peer: SyncPeer, from_height: int, to_height: int) -> List[SyncBlock]:
        """Lädt Blocks from_height..to_height von einem Peer."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.TIMEOUT)
            msg = json.dumps({
                "type": "REQUEST_BLOCKS",
                "from": from_height, "to": to_height,
                "node_id": self.node_id,
            }).encode()
            sock.sendto(msg, (peer.host, peer.port))
            data, _ = sock.recvfrom(1_000_000)
            resp = json.loads(data.decode())
            blocks = []
            for b in resp.get("blocks", []):
                blocks.append(SyncBlock(
                    height=b["height"], hash=b["hash"],
                    prev_hash=b["prev_hash"], timestamp=b["timestamp"],
                    data=b.get("data", {}),
                ))
            return blocks
        except Exception as e:
            logger.warning(f"[Sync] Fetch-Fehler von {peer.host}: {e}")
            return []
        finally:
            sock.close()

    def _best_peer(self) -> Optional[SyncPeer]:
        """Wählt Peer mit höchster Chain + niedrigster Latenz."""
        if not self.peers: return None
        # Höhen abfragen (parallel)
        threads = []
        for peer in self.peers:
            def query(p=peer):
                h = self._query_peer_height(p)
                p.height = h
            t = threading.Thread(target=query, daemon=True)
            t.start(); threads.append(t)
        for t in threads: t.join(timeout=self.TIMEOUT + 1)

        candidates = [p for p in self.peers if p.height > self.current_height]
        if not candidates: return None
        # Bester = höchste Höhe, bei Gleichstand: niedrigste Latenz
        return max(candidates, key=lambda p: (p.height, -p.latency_ms))

    def sync(self) -> bool:
        """Startet die Synchronisation. Gibt True zurück bei Erfolg."""
        self._running = True
        logger.info(f"[Sync] Start von Höhe {self.current_height}")

        peer = self._best_peer()
        if not peer:
            logger.info("[Sync] Kein besserer Peer gefunden — bereits aktuell")
            self._running = False
            return True

        target_height = peer.height
        logger.info(f"[Sync] Lade Blocks {self.current_height+1}..{target_height} von {peer.host}")
        total = target_height - self.current_height

        height = self.current_height + 1
        while height <= target_height and self._running:
            batch_end = min(height + self.BATCH_SIZE - 1, target_height)
            for attempt in range(self.MAX_RETRIES):
                blocks = self._fetch_blocks(peer, height, batch_end)
                if blocks: break
                time.sleep(0.5 * (attempt + 1))
            else:
                logger.error(f"[Sync] Batch {height}..{batch_end} fehlgeschlagen nach {self.MAX_RETRIES} Versuchen")
                self._running = False
                return False

            for block in blocks:
                if self._on_block:
                    try: self._on_block(block)
                    except Exception as e:
                        logger.error(f"[Sync] Block #{block.height} apply-Fehler: {e}")
                        self._running = False
                        return False
                self.current_height = block.height
                self._progress = int((self.current_height - (target_height - total)) / total * 100)

            height = batch_end + 1
            logger.info(f"[Sync] Fortschritt: {self._progress}% (Höhe {self.current_height}/{target_height})")

        self._running = False
        if self._on_done: self._on_done(self.current_height)
        logger.info(f"[Sync] ✅ Synchronisation abgeschlossen. Höhe: {self.current_height}")
        return True

    @property
    def progress(self) -> int:
        return self._progress

    def stop(self): self._running = False
