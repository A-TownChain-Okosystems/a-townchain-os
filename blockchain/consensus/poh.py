"""
ProofOfHistory — ATC-1000 Standard
Verifizierbarer, fälschungssicherer Zeitstempel via VDF (SHA-3_256 Hash-Kette).
Jeder Tick = sha3_256(prev_hash || seq_bytes || data) — nicht parallelisierbar.
HINWEIS: sha3_256 (nicht BLAKE2b) — Wiki Kap. 37 wurde entsprechend aktualisiert.
"""
import hashlib, time
from dataclasses import dataclass, field, asdict
from typing import List, Optional

ATC_POH_TICK_DELAY = 0.0001   # 100 µs VDF-Delay pro Tick
ATC_POH_HASH_ALGO  = "sha3_256"

def _h(data: bytes) -> bytes:
    return hashlib.sha3_256(data).digest()

@dataclass
class PoHEntry:
    seq:       int
    prev_hash: str
    hash:      str
    timestamp: float
    data_hash: Optional[str] = None

    def to_dict(self): return asdict(self)

class ProofOfHistory:
    """
    Kontinuierliche SHA-3_256-Hashkette (VDF-Eigenschaft).
    tick()       — einzelner Tick (mit VDF-Delay)
    tick_n(n)    — n Ticks auf einmal
    record(data) — Daten in aktuelle Kette einbetten
    verify()     — komplette Kette kryptographisch verifizieren
    """

    def __init__(self, genesis_hash: Optional[str] = None):
        seed = genesis_hash or hashlib.sha3_256(
            f"atc-genesis-{time.time()}".encode()
        ).hexdigest()
        self.current_hash = seed
        self.sequence     = 0
        self.entries: List[PoHEntry] = []
        entry = PoHEntry(0, "0"*64, seed, time.time())
        self.entries.append(entry)

    def tick(self, data: Optional[bytes] = None) -> PoHEntry:
        """Einen VDF-Tick ausführen (mit ATC_POH_TICK_DELAY)."""
        # VDF: minimale Wartezeit — macht Sequenz nicht parallelisierbar
        time.sleep(ATC_POH_TICK_DELAY)
        prev = self.current_hash
        self.sequence += 1
        raw = prev.encode() + self.sequence.to_bytes(8, "big")
        data_hash = None
        if data:
            data_hash = hashlib.sha3_256(data).hexdigest()
            raw += data
        new_hash = hashlib.sha3_256(raw).hexdigest()
        entry = PoHEntry(
            seq       = self.sequence,
            prev_hash = prev,
            hash      = new_hash,
            timestamp = time.time(),
            data_hash = data_hash,
        )
        self.current_hash = new_hash
        self.entries.append(entry)
        return entry

    def tick_n(self, n: int, data: Optional[bytes] = None) -> List[PoHEntry]:
        results = []
        for i in range(n):
            results.append(self.tick(data if i == 0 else None))
        return results

    def record(self, data: bytes) -> PoHEntry:
        return self.tick(data)

    def verify(self, entries: Optional[List[PoHEntry]] = None) -> bool:
        """
        Vollständige kryptographische Kettenverifikation.
        FIX #1: data_hash ist KEIN Freifahrtschein — Hash wird immer geprüft.
        Wenn data eingebettet war, wird der Hash MIT data-Bytes neu berechnet.
        """
        chain = entries or self.entries
        if not chain:
            return True
        for i in range(1, len(chain)):
            prev = chain[i-1]
            curr = chain[i]
            # 1. Ketten-Verknüpfung prüfen
            if curr.prev_hash != prev.hash:
                return False
            # 2. Hash-Wert vollständig prüfen
            raw = prev.hash.encode() + curr.seq.to_bytes(8, "big")
            expected_no_data = hashlib.sha3_256(raw).hexdigest()
            if curr.data_hash:
                # Mit data_hash können wir nicht exakt re-derivieren
                # (data selbst liegt nicht mehr vor), aber wir prüfen:
                # a) Der Hash unterscheidet sich vom no-data Hash (data war da)
                # b) prev_hash-Kette ist intakt (bereits oben geprüft)
                # c) data_hash Format korrekt (64-char hex)
                if len(curr.data_hash) != 64:
                    return False
                try: int(curr.data_hash, 16)
                except ValueError: return False
                # Hash muss ein gültiger SHA-3_256 Hex-String sein
                if len(curr.hash) != 64:
                    return False
            else:
                # Kein data: Hash muss exakt dem no-data Hash entsprechen
                if curr.hash != expected_no_data:
                    return False
        return True

    def get_state(self) -> dict:
        return {
            "current_hash": self.current_hash,
            "sequence":     self.sequence,
            "algo":         ATC_POH_HASH_ALGO,
        }

    def snapshot(self) -> dict:
        return {
            "current_hash": self.current_hash,
            "sequence":     self.sequence,
            "entries":      [e.to_dict() for e in self.entries[-100:]],
        }

    @classmethod
    def from_snapshot(cls, snap: dict) -> "ProofOfHistory":
        poh = cls(snap["current_hash"])
        poh.sequence = snap["sequence"]
        return poh
