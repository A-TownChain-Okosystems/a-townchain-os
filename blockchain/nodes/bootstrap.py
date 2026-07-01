"""
A-TownChain — Bootstrap-Node: DNS Seed & Peer Discovery (Fix #68)
Implementiert: DNS Seed, Hardcoded Fallbacks, AddrMan, Gossip

Protokoll:
  1. DNS-Lookup auf atc-seed.atownchain.io → initiale Peer-Liste
  2. Fallback: Hardcoded Bootstrap-Nodes (zensurresistent)
  3. AddrMan: persistente Peer-Verwaltung (peers.dat)
  4. Gossip: getaddr/addr Messages (bis 1000 IPs)
  5. Kademlia DHT: K=20, Alpha=3 (nach initaler Discovery)

Standard: ATC-0001, ATC-NET-001
Version:  v3.2.1 | Fix #68
"""
from __future__ import annotations
import socket, json, time, hashlib, threading, os, struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path

# ── Konfiguration ──────────────────────────────────
BOOTSTRAP_CONFIG = {
    # DNS Seeds (wie Bitcoin: mehrere unabhängige Betreiber)
    "dns_seeds": [
        "seed1.atownchain.io",
        "seed2.atownchain.io",
        "seed3.atownchain.io",
        "dnsseed.atc-chain.net",
        "atc-seed.shivacore.dev",
    ],
    # Hardcoded Fallback-Nodes (zensurresistent, wie Bitcoin Core)
    "hardcoded_seeds": [
        ("5.9.104.210",   5005),   # Validator-1 (Frankfurt)
        ("95.217.12.33",  5005),   # Validator-2 (Helsinki)
        ("144.76.21.88",  5005),   # Full-Node   (Nuremberg)
        ("148.251.190.4", 5005),   # Archive     (Falkenstein)
        ("78.46.222.55",  5005),   # Bootstrap   (Frankfurt)
    ],
    "bootstrap_port":       5005,
    "p2p_port":             4001,
    "max_outbound_peers":   8,
    "max_inbound_peers":    125,
    "peer_timeout_sec":     90,
    "handshake_timeout_sec":10,
    "addr_max_per_msg":     1000,   # max IPs pro addr-Message
    "addrman_path":         "data/peers.dat",
    "dns_timeout_sec":      5,
    "dns_retry":            3,
    "kademlia_k":           20,
    "kademlia_alpha":       3,
}

@dataclass
class PeerAddress:
    """Eine bekannte Peer-Adresse im Netzwerk."""
    ip:           str
    port:         int
    last_seen:    int   = field(default_factory=lambda: int(time.time()))
    last_tried:   int   = 0
    attempt_count:int   = 0
    connected:    bool  = False
    services:     int   = 0x01    # NODE_NETWORK
    version:      str   = "3.2.1"
    source:       str   = "unknown"   # dns|hardcoded|gossip|manual

    @property
    def address(self) -> Tuple[str, int]:
        return (self.ip, self.port)

    @property
    def is_stale(self) -> bool:
        """Adresse gilt als veraltet wenn > 14 Tage nicht gesehen."""
        return (int(time.time()) - self.last_seen) > 14 * 86400

    @property
    def key(self) -> str:
        return f"{self.ip}:{self.port}"

    def to_dict(self) -> dict:
        return {
            "ip": self.ip, "port": self.port,
            "last_seen": self.last_seen, "last_tried": self.last_tried,
            "attempt_count": self.attempt_count, "services": self.services,
            "source": self.source, "version": self.version,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PeerAddress":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


class AddrMan:
    """
    Peer Address Manager — persistente Verwaltung aller bekannten Nodes.

    Wie Bitcoin Core AddrMan:
      new_table:  Unverbundene Adressen (von Seeds / Gossip)
      tried_table: Bestätigte Verbindungen
      Persistenz: peers.dat (JSON, atomares Schreiben)
    """

    def __init__(self, path: str = BOOTSTRAP_CONFIG["addrman_path"]):
        self.path         = Path(path)
        self.new_table:   Dict[str, PeerAddress] = {}
        self.tried_table: Dict[str, PeerAddress] = {}
        self._lock        = threading.Lock()
        self._load()

    def _load(self):
        """Lädt peers.dat beim Start."""
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text())
                for d in raw.get("new", []):
                    p = PeerAddress.from_dict(d)
                    self.new_table[p.key] = p
                for d in raw.get("tried", []):
                    p = PeerAddress.from_dict(d)
                    self.tried_table[p.key] = p
            except Exception:
                pass  # Korrupte Datei → leer starten

    def save(self):
        """Schreibt peers.dat atomar."""
        with self._lock:
            tmp = self.path.with_suffix('.tmp')
            self.path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "new":   [p.to_dict() for p in self.new_table.values()],
                "tried": [p.to_dict() for p in self.tried_table.values()],
                "saved_at": int(time.time()),
                "version":  "3.2.1",
            }
            tmp.write_text(json.dumps(data, indent=2))
            tmp.replace(self.path)   # atomares Ersetzen

    def add(self, peer: PeerAddress):
        """Fügt Adresse zur new_table hinzu (wenn nicht schon in tried)."""
        with self._lock:
            if peer.key in self.tried_table:
                return
            if peer.key not in self.new_table:
                self.new_table[peer.key] = peer

    def mark_tried(self, key: str):
        """Verschiebt Adresse in tried_table nach erfolgreicher Verbindung."""
        with self._lock:
            peer = self.new_table.pop(key, None) or self.tried_table.get(key)
            if peer:
                peer.connected  = True
                peer.last_seen  = int(time.time())
                self.tried_table[key] = peer

    def mark_failed(self, key: str):
        """Erhöht Fehler-Zähler; entfernt nach 3 Fehlversuchen."""
        with self._lock:
            peer = self.new_table.get(key) or self.tried_table.get(key)
            if peer:
                peer.attempt_count += 1
                peer.last_tried     = int(time.time())
                if peer.attempt_count >= 3:
                    self.new_table.pop(key, None)
                    self.tried_table.pop(key, None)

    def get_candidates(self, n: int = 10) -> List[PeerAddress]:
        """Liefert n Kandidaten für ausgehende Verbindungen."""
        with self._lock:
            # tried_table bevorzugen (bekannte Nodes)
            candidates = list(self.tried_table.values())
            candidates += list(self.new_table.values())
            # Frischeste zuerst, stalte herausfiltern
            fresh = [p for p in candidates if not p.is_stale]
            fresh.sort(key=lambda p: p.last_seen, reverse=True)
            return fresh[:n]

    def get_addr_sample(self, max_count: int = 1000) -> List[dict]:
        """Liefert zufällige Stichprobe für addr-Gossip-Messages."""
        import random
        with self._lock:
            all_peers = list(self.tried_table.values()) + list(self.new_table.values())
            sample    = random.sample(all_peers, min(max_count, len(all_peers)))
            return [{"ip": p.ip, "port": p.port, "last_seen": p.last_seen} for p in sample]

    @property
    def stats(self) -> dict:
        return {
            "new_count":   len(self.new_table),
            "tried_count": len(self.tried_table),
            "total":       len(self.new_table) + len(self.tried_table),
        }


class DNSSeedResolver:
    """
    DNS Seed Resolver — löst Seed-Hostnamen zu IP-Listen auf.

    Wie Bitcoin:
      - Mehrere unabhängige DNS-Seed-Betreiber
      - Bei DNS-Ausfall: automatischer Fallback auf hardcoded Seeds
      - Timeout + Retry-Logik
    """

    def __init__(self, seeds=None, timeout=None):
        self.seeds   = seeds   or BOOTSTRAP_CONFIG["dns_seeds"]
        self.timeout = timeout or BOOTSTRAP_CONFIG["dns_timeout_sec"]
        self.port    = BOOTSTRAP_CONFIG["bootstrap_port"]

    def resolve_seed(self, hostname: str) -> List[PeerAddress]:
        """Löst einen DNS-Seed-Hostname auf."""
        peers = []
        for attempt in range(BOOTSTRAP_CONFIG["dns_retry"]):
            try:
                socket.setdefaulttimeout(self.timeout)
                infos = socket.getaddrinfo(hostname, self.port,
                                           proto=socket.IPPROTO_TCP)
                for info in infos:
                    ip = info[4][0]
                    if self._is_valid_ip(ip):
                        peers.append(PeerAddress(
                            ip=ip, port=self.port, source="dns",
                            last_seen=int(time.time())
                        ))
                if peers:
                    return peers
            except (socket.gaierror, socket.timeout, OSError):
                if attempt < BOOTSTRAP_CONFIG["dns_retry"] - 1:
                    time.sleep(0.5)
        return []

    def resolve_all(self) -> List[PeerAddress]:
        """Löst alle DNS Seeds auf; bricht bei erster Erfolg nicht ab."""
        all_peers: List[PeerAddress] = []
        seen_ips:  Set[str] = set()
        for seed in self.seeds:
            peers = self.resolve_seed(seed)
            for p in peers:
                if p.ip not in seen_ips:
                    all_peers.append(p)
                    seen_ips.add(p.ip)
        return all_peers

    @staticmethod
    def _is_valid_ip(ip: str) -> bool:
        """Prüft ob IP gültig und nicht privat/loopback."""
        try:
            parts = ip.split('.')
            if len(parts) == 4:
                nums = [int(p) for p in parts]
                if nums[0] in (10, 127):      return False  # loopback/private
                if nums[0] == 172 and 16 <= nums[1] <= 31: return False
                if nums[0] == 192 and nums[1] == 168:      return False
                return all(0 <= n <= 255 for n in nums)
            return False
        except ValueError:
            return False

    def get_hardcoded_seeds(self) -> List[PeerAddress]:
        """Gibt hardcoded Fallback-Nodes zurück."""
        return [
            PeerAddress(ip=ip, port=port, source="hardcoded",
                        last_seen=int(time.time()))
            for ip, port in BOOTSTRAP_CONFIG["hardcoded_seeds"]
        ]


class BootstrapNode:
    """
    A-TownChain Bootstrap-Node (Fix #68).

    Startup-Sequenz:
      1. AddrMan laden (peers.dat)
      2. DNS Seeds auflösen → neue Peers in AddrMan
      3. Falls DNS fehlschlägt → hardcoded Seeds verwenden
      4. Ausgehende Verbindungen zu Kandidaten aufbauen
      5. getaddr senden → weitere Peers empfangen
      6. Peers via addr-Gossip propagieren (max 1000/msg)
      7. AddrMan periodisch speichern (alle 15min)
    """

    def __init__(self, node_id: str = "", data_dir: str = "data"):
        self.node_id   = node_id or self._gen_node_id()
        self.addrman   = AddrMan(f"{data_dir}/peers.dat")
        self.resolver  = DNSSeedResolver()
        self.connected: Dict[str, PeerAddress] = {}
        self._running  = False
        self._lock     = threading.Lock()

    @staticmethod
    def _gen_node_id() -> str:
        return "ATC-NODE-" + hashlib.sha3_256(
            str(time.time()).encode()
        ).hexdigest()[:16].upper()

    def bootstrap(self) -> dict:
        """
        Führt vollständige Bootstrap-Sequenz durch.
        Gibt Statistik zurück.
        """
        result = {"dns_peers": 0, "hardcoded_peers": 0,
                  "total_known": 0, "source": ""}

        # Schritt 1: DNS Seeds
        dns_peers = self.resolver.resolve_all()
        if dns_peers:
            for p in dns_peers:
                self.addrman.add(p)
            result["dns_peers"]  = len(dns_peers)
            result["source"]     = "dns"
        else:
            # Schritt 2: Fallback auf hardcoded Seeds
            hardcoded = self.resolver.get_hardcoded_seeds()
            for p in hardcoded:
                self.addrman.add(p)
            result["hardcoded_peers"] = len(hardcoded)
            result["source"]          = "hardcoded_fallback"

        result["total_known"] = self.addrman.stats["total"]
        self.addrman.save()
        return result

    def handle_getaddr(self, requester_ip: str) -> List[dict]:
        """
        Verarbeitet getaddr-Message eines Peers.
        Antwortet mit bis zu 1000 bekannten Adressen (addr-Message).
        """
        sample = self.addrman.get_addr_sample(
            BOOTSTRAP_CONFIG["addr_max_per_msg"]
        )
        # Eigene Adresse nicht mitschicken
        return [p for p in sample if p["ip"] != requester_ip]

    def handle_addr(self, peers: List[dict], source_ip: str):
        """
        Verarbeitet eingehende addr-Message mit neuen Peer-Adressen.
        Fügt valide, neue Adressen dem AddrMan hinzu.
        """
        added = 0
        for p_data in peers[:BOOTSTRAP_CONFIG["addr_max_per_msg"]]:
            ip   = p_data.get("ip","")
            port = p_data.get("port", BOOTSTRAP_CONFIG["p2p_port"])
            if DNSSeedResolver._is_valid_ip(ip) and 1024 <= port <= 65535:
                peer = PeerAddress(ip=ip, port=port,
                                   source=f"gossip:{source_ip}",
                                   last_seen=int(time.time()))
                self.addrman.add(peer)
                added += 1
        if added:
            self.addrman.save()
        return added

    def get_peers_for_new_node(self, requesting_ip: str,
                                count: int = 25) -> List[dict]:
        """
        Gibt einem neuen Node eine Liste von Peers zurück.
        Priorisiert tried_table (bekannte, verbundene Nodes).
        """
        candidates = self.addrman.get_candidates(count * 2)
        result     = []
        for p in candidates:
            if p.ip != requesting_ip:
                result.append({"ip": p.ip, "port": p.port,
                               "services": p.services,
                               "last_seen": p.last_seen})
            if len(result) >= count:
                break
        return result

    def mark_peer_connected(self, ip: str, port: int):
        key = f"{ip}:{port}"
        self.addrman.mark_tried(key)
        with self._lock:
            self.connected[key] = PeerAddress(ip=ip, port=port,
                connected=True, last_seen=int(time.time()))

    def mark_peer_failed(self, ip: str, port: int):
        self.addrman.mark_failed(f"{ip}:{port}")
        with self._lock:
            self.connected.pop(f"{ip}:{port}", None)

    def get_status(self) -> dict:
        stats = self.addrman.stats
        return {
            "node_id":        self.node_id,
            "connected_peers":len(self.connected),
            "known_peers":    stats["total"],
            "new_peers":      stats["new_count"],
            "tried_peers":    stats["tried_count"],
            "config": {
                "bootstrap_port": BOOTSTRAP_CONFIG["bootstrap_port"],
                "p2p_port":       BOOTSTRAP_CONFIG["p2p_port"],
                "kademlia_k":     BOOTSTRAP_CONFIG["kademlia_k"],
                "kademlia_alpha": BOOTSTRAP_CONFIG["kademlia_alpha"],
                "dns_seeds":      len(BOOTSTRAP_CONFIG["dns_seeds"]),
                "hardcoded_seeds":len(BOOTSTRAP_CONFIG["hardcoded_seeds"]),
            }
        }
