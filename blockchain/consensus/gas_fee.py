"""
Gas-Fee Mechanismus — Issue #33 (Kap. 4 Blockchain)
EIP-1559-inspiriertes Gas-Modell für A-TownChain.
Base Fee + Priority Fee + Fee Burning.
"""
import math, time
from dataclasses import dataclass
from typing import Optional

@dataclass
class GasConfig:
    """Netzwerk-weite Gas-Konfiguration."""
    base_fee:         float = 0.001    # ATC / Gas-Unit (initial)
    min_base_fee:     float = 0.0001
    max_base_fee:     float = 1.0
    gas_limit_block:  int   = 10_000_000  # Max Gas pro Block
    gas_target:       int   = 5_000_000   # Ziel-Gas pro Block (50%)
    elasticity:       int   = 2            # Max Abweichung vom Ziel
    base_fee_change:  float = 0.125        # Max ±12.5% pro Block

@dataclass
class GasEstimate:
    gas_units:    int
    base_fee:     float
    priority_fee: float
    max_fee:      float
    total_cost:   float
    burned:       float
    miner_reward: float

class GasFeeEngine:
    """
    A-TownChain Gas-Fee Engine (ATC-GAS-1000).
    Kompatibel mit EIP-1559-Semantik.
    Implementiert:
    - Dynamische Base Fee (passt sich ans Netz-Auslastung an)
    - Priority Fee (Miner-Trinkgeld)
    - Fee Burning (Deflation: 50% der Base Fee wird verbrannt)
    """

    # Gas-Preise für Standard-Operationen (in Gas-Units)
    GAS_TABLE = {
        "transfer":         21_000,
        "contract_call":   100_000,
        "contract_deploy": 500_000,
        "storage_write":    20_000,
        "storage_read":      5_000,
        "event_emit":       10_000,
        "validator_vote":   15_000,
        "nft_mint":         80_000,
        "nft_transfer":     40_000,
        "bridge_lock":     150_000,
        "dao_vote":         25_000,
    }

    def __init__(self, config: Optional[GasConfig] = None):
        self.config    = config or GasConfig()
        self.base_fee  = self.config.base_fee
        self._history  = []   # (timestamp, gas_used, base_fee)
        self._burned   = 0.0  # Gesamt verbrannte ATC
        self._collected= 0.0  # Gesamt Miner-Rewards

    def estimate_gas(self, operation: str, data_size: int = 0) -> int:
        """Gas-Units für Operation schätzen."""
        base = self.GAS_TABLE.get(operation, 50_000)
        # Datenmenge: +16 Gas/Byte
        return base + data_size * 16

    def estimate_fee(self, gas_units: int,
                      priority_fee: float = 0.001) -> GasEstimate:
        """Vollständige Fee-Schätzung."""
        total_fee    = gas_units * (self.base_fee + priority_fee)
        burned       = gas_units * self.base_fee * 0.5  # 50% verbrennen
        miner_reward = total_fee - burned
        return GasEstimate(
            gas_units    = gas_units,
            base_fee     = self.base_fee,
            priority_fee = priority_fee,
            max_fee      = self.base_fee * 2 + priority_fee,
            total_cost   = round(total_fee, 8),
            burned       = round(burned, 8),
            miner_reward = round(miner_reward, 8),
        )

    def apply_block(self, gas_used: int) -> float:
        """
        Nach jedem Block Base Fee anpassen (EIP-1559).
        Gas-Used > Gas-Target → Fee steigt
        Gas-Used < Gas-Target → Fee sinkt
        """
        target   = self.config.gas_target
        old_fee  = self.base_fee
        delta    = (gas_used - target) / target  # -1..+1 normiert
        change   = old_fee * self.config.base_fee_change * delta
        new_fee  = old_fee + change
        new_fee  = max(self.config.min_base_fee,
                       min(self.config.max_base_fee, new_fee))
        self.base_fee = round(new_fee, 8)
        self._history.append((time.time(), gas_used, self.base_fee))
        return self.base_fee

    def process_tx(self, gas_units: int, priority_fee: float = 0.001) -> dict:
        """Transaktion verarbeiten: Fee berechnen + Burning buchen."""
        est = self.estimate_fee(gas_units, priority_fee)
        self._burned   += est.burned
        self._collected+= est.miner_reward
        return {
            "fee_paid":     est.total_cost,
            "burned":       est.burned,
            "miner_reward": est.miner_reward,
            "base_fee":     self.base_fee,
        }

    def stats(self) -> dict:
        return {
            "current_base_fee": self.base_fee,
            "total_burned_atc": round(self._burned, 6),
            "total_miner_rewards": round(self._collected, 6),
            "block_history":   len(self._history),
            "gas_operations":  list(self.GAS_TABLE.keys()),
        }
