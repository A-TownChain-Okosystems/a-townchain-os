"""
Mainnet Launch Manager — Issue #52 (Kap. 46)
Genesis-Block-Generierung, Validator-Aktivierung, MainNet-Start.
"""
import hashlib, json, time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

class LaunchPhase(Enum):
    SETUP         = "setup"         # Konfiguration
    GENESIS       = "genesis"       # Genesis-Block erzeugt
    VALIDATORS    = "validators"    # Alle Validatoren am Netz
    CONSENSUS     = "consensus"     # Konsensus-Check bestanden
    READY         = "ready"         # Mainnet-Start freigegeben
    LAUNCHED      = "launched"      # Live

@dataclass
class GenesisBlock:
    """Mainnet Genesis-Block (Block #0)."""
    chain_id:        str
    timestamp:       float
    validators:      List[str]           # Gültige Validator-Adressen
    initial_supply:  float               # ATC in Zirkulation
    allocation:      Dict[str, float]    # address → amount
    config:          dict = field(default_factory=dict)  # Network-Parameter
    hash:            str = ""
    merkle_root:     str = ""

    def __post_init__(self):
        if not self.hash:
            self.compute_hash()
        if not self.merkle_root:
            self.compute_merkle_root()

    def compute_hash(self):
        """Genesis-Block Hash (SHA-256)."""
        data = f"{self.chain_id}{self.timestamp}{len(self.validators)}{self.initial_supply}"
        self.hash = hashlib.sha256(data.encode()).hexdigest()

    def compute_merkle_root(self):
        """Merkle Root über alle Allocations."""
        leaves = sorted(
            [hashlib.sha256(f"{addr}{amt}".encode()).hexdigest()
             for addr, amt in self.allocation.items()]
        )
        while len(leaves) > 1:
            next_level = []
            for i in range(0, len(leaves), 2):
                if i + 1 < len(leaves):
                    combined = hashlib.sha256(
                        f"{leaves[i]}{leaves[i+1]}".encode()
                    ).hexdigest()
                else:
                    combined = leaves[i]
                next_level.append(combined)
            leaves = next_level
        self.merkle_root = leaves[0] if leaves else ""

    def to_json(self) -> str:
        return json.dumps({
            "chain_id": self.chain_id,
            "timestamp": self.timestamp,
            "validators": self.validators,
            "initial_supply": self.initial_supply,
            "allocation": self.allocation,
            "hash": self.hash,
            "merkle_root": self.merkle_root,
            "config": self.config,
        }, indent=2)


class MainnetLaunchManager:
    """
    Mainnet Launch Manager — ATC-MAIN-1000.
    Orchestriert den kontrollierten Launch vom Testnet zum Mainnet.
    """
    REQUIRED_VALIDATORS = 3   # Min. Validatoren
    REQUIRED_FULL_NODES = 5   # Min. Full Nodes
    CONSENSUS_THRESHOLD = 0.67  # 67% Validator-Zustimmung

    def __init__(self, chain_id: str = "atc-mainnet-1"):
        self.chain_id    = chain_id
        self.phase       = LaunchPhase.SETUP
        self.genesis:    Optional[GenesisBlock] = None
        self._validators: Dict[str, dict] = {}  # addr → {pubkey, stake, active}
        self._nodes:     Dict[str, dict] = {}   # node_id → {type, status}
        self._votes:     Dict[str, bool] = {}   # validator → approved
        self._launch_at  = None
        self._checksums  = {}

    def add_validator(self, address: str, pubkey: str, stake: float = 1000.0):
        """Validator registrieren."""
        self._validators[address] = {
            "pubkey": pubkey,
            "stake": stake,
            "active": False,
            "joined_at": time.time(),
        }

    def add_node(self, node_id: str, node_type: str, address: str):
        """Full Node registrieren."""
        self._nodes[node_id] = {
            "type": node_type,  # "validator" | "full" | "archive"
            "status": "pending",
            "address": address,
            "synced": False,
        }

    def create_genesis(self, allocation: Dict[str, float]) -> GenesisBlock:
        """Genesis-Block erzeugen."""
        if self.phase != LaunchPhase.SETUP:
            raise ValueError(f"Genesis nur in SETUP Phase möglich")

        validators = list(self._validators.keys())
        if len(validators) < self.REQUIRED_VALIDATORS:
            raise ValueError(f"Min. {self.REQUIRED_VALIDATORS} Validatoren erforderlich")

        total_supply = sum(allocation.values())

        self.genesis = GenesisBlock(
            chain_id=self.chain_id,
            timestamp=time.time(),
            validators=validators,
            initial_supply=total_supply,
            allocation=allocation,
            config={
                "block_time": 5,
                "gas_limit": 10_000_000,
                "min_fee": 0.0001,
                "required_signatures": max(1, len(validators) // 2 + 1),
            }
        )
        self.phase = LaunchPhase.GENESIS
        return self.genesis

    def activate_validators(self) -> int:
        """Alle Validatoren aktivieren."""
        if not self.genesis:
            raise ValueError("Genesis-Block erforderlich")

        activated = 0
        for addr in self.genesis.validators:
            if addr in self._validators:
                self._validators[addr]["active"] = True
                activated += 1

        if activated >= self.REQUIRED_VALIDATORS:
            self.phase = LaunchPhase.VALIDATORS
        return activated

    def sync_nodes(self) -> int:
        """Alle Nodes zur Genesis synchronisieren."""
        synced = 0
        for node_id, node in self._nodes.items():
            node["synced"] = True
            node["status"] = "synced"
            synced += 1
        return synced

    def validator_vote(self, validator_address: str, approved: bool):
        """Validator stimmt für Mainnet-Launch ab."""
        if validator_address not in self._validators:
            raise ValueError("Validator nicht registriert")
        self._votes[validator_address] = approved

    def check_consensus(self) -> bool:
        """Konsensus-Check: >=67% Zustimmung."""
        if not self._validators:
            return False
        approval_count = sum(1 for v in self._votes.values() if v)
        approval_pct = approval_count / len(self._validators)
        return approval_pct >= self.CONSENSUS_THRESHOLD

    def check_readiness(self) -> dict:
        """Mainnet-Readiness-Prüfung."""
        checks = {
            "genesis_ready": self.genesis is not None,
            "validators_active": sum(1 for v in self._validators.values() if v["active"]) >= self.REQUIRED_VALIDATORS,
            "nodes_synced": sum(1 for n in self._nodes.values() if n["synced"]) >= self.REQUIRED_FULL_NODES,
            "consensus_reached": self.check_consensus(),
            "phase": self.phase.value,
        }
        all_ready = all(checks.values())
        if all_ready:
            self.phase = LaunchPhase.READY
        return checks

    def launch(self, scheduled_time: Optional[float] = None) -> dict:
        """Mainnet-Launch durchführen."""
        if self.phase != LaunchPhase.READY:
            raise ValueError(f"Nur in READY Phase möglich (aktuell: {self.phase.value})")

        self._launch_at = scheduled_time or time.time()
        self.phase = LaunchPhase.LAUNCHED

        return {
            "status": "launched",
            "chain_id": self.chain_id,
            "genesis_hash": self.genesis.hash,
            "validators": len(self.genesis.validators),
            "initial_supply": self.genesis.initial_supply,
            "launch_timestamp": self._launch_at,
            "launch_block": 0,
        }

    def export_genesis_json(self) -> str:
        """Genesis-JSON für Nodes exportieren."""
        if not self.genesis:
            raise ValueError("Genesis-Block nicht vorhanden")
        return self.genesis.to_json()

    def stats(self) -> dict:
        return {
            "chain_id": self.chain_id,
            "phase": self.phase.value,
            "validators": len(self._validators),
            "active_validators": sum(1 for v in self._validators.values() if v["active"]),
            "nodes": len(self._nodes),
            "synced_nodes": sum(1 for n in self._nodes.values() if n["synced"]),
            "votes": len(self._votes),
            "consensus_reached": self.check_consensus(),
            "genesis": self.genesis is not None,
        }
