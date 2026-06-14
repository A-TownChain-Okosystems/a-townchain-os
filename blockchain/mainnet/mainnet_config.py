"""
A-TownChain — Mainnet Launch Configuration (Fix #36)
Chain-ID: 9000 | Genesis Block | Validator-Set | Token Distribution

HINWEIS: Mainnet-Launch erfordert externes Security-Audit.
         Diese Datei enthält die vollständige Launch-Konfiguration.
"""
from __future__ import annotations
import hashlib, time, json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ── Mainnet-Konfiguration ──────────────────────────
MAINNET_CONFIG = {
    "chain_id":           9000,
    "chain_name":         "A-TownChain Mainnet",
    "symbol":             "ATC",
    "decimals":           18,
    "version":            "1.0.0",
    "launch_date":        None,  # Wird bei Launch gesetzt
    "network_id":         9000,
    "genesis_hash":       None,  # Wird bei Genesis generiert

    # Konsens
    "consensus":          "ShivaConsensus-v2",
    "block_time_target":  1000,  # 1 Sekunde (Ziel)
    "max_block_size":     2_097_152,  # 2 MB
    "max_tx_per_block":   5000,

    # Gas
    "initial_base_fee":   1_000_000_000,  # 1 Gwei
    "min_gas_price":      100_000_000,    # 0.1 Gwei
    "gas_limit_per_block":10_000_000,
    "burn_rate":          0.50,           # 50% Base Fee Burn

    # Validatoren
    "min_validator_stake":  10_000 * 10**18,   # 10.000 ATC
    "initial_validators":   10,
    "max_validators":       100,
    "validator_reward":     0.02,   # 2% APY

    # Token
    "total_supply":         21_000_000 * 10**18,  # 21M ATC
    "initial_circulation":   5_250_000 * 10**18,  # 25% bei Launch

    # Security
    "bft_threshold":        0.67,   # 2/3 + 1 Mehrheit
    "min_nodes_for_launch": 10,
    "audit_required":       True,
}

# Token-Verteilung (Tokenomics)
TOKEN_DISTRIBUTION = {
    "community":       0.40,   # 40% — Community + Ecosystem
    "team":            0.15,   # 15% — Team (4-Jahres-Vesting)
    "validators":      0.20,   # 20% — Validator-Staking-Rewards
    "treasury":        0.15,   # 15% — DAO Treasury
    "liquidity":       0.05,   # 5%  — DEX Liquidity
    "franchise":       0.05,   # 5%  — Franchise Factory
}

@dataclass
class GenesisBlock:
    """Genesis Block (Block 0) von A-TownChain Mainnet."""
    chain_id:        int   = 9000
    height:          int   = 0
    timestamp:       int   = field(default_factory=lambda: int(time.time()))
    prev_hash:       str   = "0" * 64
    transactions:    list  = field(default_factory=list)
    validators:      list  = field(default_factory=list)
    config:          dict  = field(default_factory=dict)
    hash_:           str   = ""
    signature:       str   = ""

    def compute_hash(self) -> str:
        header = json.dumps({
            "chain_id":   self.chain_id,
            "height":     self.height,
            "timestamp":  self.timestamp,
            "prev_hash":  self.prev_hash,
            "validators": sorted(self.validators),
        }, sort_keys=True)
        return "ATC" + hashlib.sha3_256(header.encode()).hexdigest()

    def finalize(self) -> "GenesisBlock":
        self.hash_ = self.compute_hash()
        return self

@dataclass
class ValidatorRegistration:
    """Validator-Registrierung für Mainnet."""
    address:      str
    stake:        int
    public_key:   str
    endpoint:     str
    region:       str
    registered:   int = field(default_factory=lambda: int(time.time()))
    active:       bool = True

    def is_eligible(self) -> bool:
        min_stake = MAINNET_CONFIG["min_validator_stake"]
        return (self.stake >= min_stake and
                self.active and
                len(self.address) == 35 and
                self.address.startswith("ATC"))

class MainnetLaunchManager:
    """
    Verwaltet den Mainnet-Launch-Prozess.

    Checkliste:
    ✅ Smart Contracts deployed (v1.0.0)
    ✅ Security Audit v1.0.0 (10 Fixes)
    ✅ 5-Node Testnet läuft stabil (v1.0.0)
    ✅ Integration Tests 9/9 bestanden
    ✅ Solana Bridge implementiert (v1.0.0)
    ✅ ATCLang v0.3.0 deployed
    ✅ DEX/AMM implementiert
    ⏳ Externes Security-Audit (ausstehend)
    ⏳ 10+ Validator-Nodes bereit
    ⏳ Genesis Block signiert
    """

    def __init__(self):
        self.validators:     Dict[str, ValidatorRegistration] = {}
        self.genesis:        Optional[GenesisBlock] = None
        self.audit_passed:   bool = False
        self.launch_ready:   bool = False
        self.launch_ts:      Optional[int] = None

    def register_validator(self, v: ValidatorRegistration) -> bool:
        if not v.is_eligible():
            raise ValueError(f"Validator {v.address} nicht berechtigt — Min-Stake: {MAINNET_CONFIG['min_validator_stake']//10**18} ATC")
        self.validators[v.address] = v
        return True

    def mark_audit_passed(self, auditor: str, date: str):
        self.audit_passed = True
        self._audit_info = {"auditor": auditor, "date": date}

    def check_launch_readiness(self) -> dict:
        n_val    = len([v for v in self.validators.values() if v.is_eligible()])
        min_val  = MAINNET_CONFIG["min_nodes_for_launch"]
        checklist = {
            "validators_ready": n_val >= min_val,
            "audit_passed":     self.audit_passed,
            "genesis_created":  self.genesis is not None,
            "config_valid":     MAINNET_CONFIG["chain_id"] == 9000,
        }
        self.launch_ready = all(checklist.values())
        return {
            "ready":     self.launch_ready,
            "checklist": checklist,
            "validators": n_val,
            "min_required": min_val,
        }

    def create_genesis(self) -> GenesisBlock:
        readiness = self.check_launch_readiness()
        if not readiness["ready"]:
            raise RuntimeError(f"Nicht bereit für Mainnet-Launch: {readiness['checklist']}")
        val_addresses = [v.address for v in self.validators.values() if v.is_eligible()]
        self.genesis = GenesisBlock(
            chain_id=9000,
            timestamp=int(time.time()),
            validators=val_addresses,
            config=MAINNET_CONFIG,
        ).finalize()
        self.launch_ts = int(time.time())
        return self.genesis

    def get_status(self) -> dict:
        n_val = len(self.validators)
        return {
            "chain_id":          MAINNET_CONFIG["chain_id"],
            "validators_count":  n_val,
            "audit_passed":      self.audit_passed,
            "genesis_created":   self.genesis is not None,
            "genesis_hash":      self.genesis.hash_ if self.genesis else None,
            "launch_ready":      self.launch_ready,
            "total_supply":      f"{MAINNET_CONFIG['total_supply']//10**18:,} ATC",
            "token_distribution": TOKEN_DISTRIBUTION,
        }
