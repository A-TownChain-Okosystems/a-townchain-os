"""
A-TownChain — DEX / AMM (Fix #37)
Constant-Product AMM: x * y = k
Swap-Router | Liquidity Pools | LP-Token | 0.3% Fee
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple
import hashlib, time, math

DEX_CONFIG = {
    "swap_fee":        30,    # 0.30% in Basis-Punkten
    "protocol_fee":    5,     # 0.05% → Treasury
    "min_liquidity":   1000,  # Minimum LP-Token (gegen Dust)
    "max_slippage":    0.05,  # 5% max Slippage
    "price_impact_warn": 0.01,  # Warnung ab 1%
}

@dataclass
class LiquidityPool:
    """
    Constant-Product AMM Pool: x * y = k

    Invariante: reserve_a * reserve_b = k (nach Fees)
    """
    pool_id:     str
    token_a:     str    # z.B. "ATC"
    token_b:     str    # z.B. "FFT"
    reserve_a:   int = 0
    reserve_b:   int = 0
    lp_supply:   int = 0
    fee_bps:     int = field(default=30)  # 0.30%
    k:           int = 0   # x * y = k
    created_at:  int = field(default_factory=lambda: int(time.time()))
    lp_balances: Dict[str, int] = field(default_factory=dict)
    fees_earned_a: int = 0
    fees_earned_b: int = 0
    _locked:     bool = False

    def _nonreentrant_enter(self):
        if self._locked: raise RuntimeError("AMM: Reentrancy nicht erlaubt")
        self._locked = True

    def _nonreentrant_exit(self):
        self._locked = False

    def _k(self) -> int:
        return self.reserve_a * self.reserve_b

    def get_price(self) -> float:
        """Spotpreis: token_b pro token_a."""
        if self.reserve_a == 0: return 0
        return self.reserve_b / self.reserve_a

    def get_price_impact(self, amount_in: int, a_to_b: bool) -> float:
        """Berechnet Price Impact in % für gegebenen Swap."""
        if a_to_b:
            amount_out = self._get_amount_out(amount_in, self.reserve_a, self.reserve_b)
            old_price  = self.reserve_b / self.reserve_a if self.reserve_a > 0 else 0
            new_res_a  = self.reserve_a + amount_in
            new_res_b  = self.reserve_b - amount_out
            new_price  = new_res_b / new_res_a if new_res_a > 0 else 0
        else:
            amount_out = self._get_amount_out(amount_in, self.reserve_b, self.reserve_a)
            old_price  = self.reserve_a / self.reserve_b if self.reserve_b > 0 else 0
            new_res_b  = self.reserve_b + amount_in
            new_res_a  = self.reserve_a - amount_out
            new_price  = new_res_a / new_res_b if new_res_b > 0 else 0
        if old_price == 0: return 0
        return abs(new_price - old_price) / old_price

    def _get_amount_out(self, amount_in: int, reserve_in: int, reserve_out: int) -> int:
        """
        AMM-Formel mit Fee:
        amount_out = (amount_in * (10000-fee) * reserve_out) /
                     (reserve_in * 10000 + amount_in * (10000-fee))
        """
        if reserve_in == 0 or reserve_out == 0:
            raise ValueError("Pool hat keine Liquidität")
        if amount_in <= 0:
            raise ValueError("amount_in muss > 0 sein")
        fee_factor  = 10000 - self.fee_bps
        numerator   = amount_in * fee_factor * reserve_out
        denominator = reserve_in * 10000 + amount_in * fee_factor
        return numerator // denominator

    def swap_a_to_b(self, amount_in: int, min_out: int,
                    trader: str) -> dict:
        """Swap token_a → token_b."""
        self._nonreentrant_enter()
        try:
            if self.reserve_a == 0 or self.reserve_b == 0:
                raise ValueError("Pool leer")
            impact = self.get_price_impact(amount_in, True)
            if impact > DEX_CONFIG["max_slippage"]:
                raise ValueError(f"Price Impact zu hoch: {impact*100:.1f}% > {DEX_CONFIG['max_slippage']*100}%")
            amount_out = self._get_amount_out(amount_in, self.reserve_a, self.reserve_b)
            if amount_out < min_out:
                raise ValueError(f"Slippage zu hoch: {amount_out} < {min_out}")
            fee_amount  = amount_in * self.fee_bps // 10000
            # State ändern VOR emit
            self.reserve_a       += amount_in
            self.reserve_b       -= amount_out
            self.fees_earned_a   += fee_amount
            self.k                = self._k()
            return {"amount_in": amount_in, "amount_out": amount_out,
                    "fee": fee_amount, "price_impact": impact, "trader": trader}
        finally:
            self._nonreentrant_exit()

    def swap_b_to_a(self, amount_in: int, min_out: int,
                    trader: str) -> dict:
        """Swap token_b → token_a."""
        self._nonreentrant_enter()
        try:
            impact     = self.get_price_impact(amount_in, False)
            if impact > DEX_CONFIG["max_slippage"]:
                raise ValueError(f"Price Impact zu hoch: {impact*100:.1f}%")
            amount_out = self._get_amount_out(amount_in, self.reserve_b, self.reserve_a)
            if amount_out < min_out:
                raise ValueError(f"Slippage: {amount_out} < {min_out}")
            fee_amount     = amount_in * self.fee_bps // 10000
            self.reserve_b += amount_in
            self.reserve_a -= amount_out
            self.fees_earned_b += fee_amount
            self.k          = self._k()
            return {"amount_in": amount_in, "amount_out": amount_out,
                    "fee": fee_amount, "price_impact": impact}
        finally:
            self._nonreentrant_exit()

    def add_liquidity(self, amount_a: int, amount_b: int,
                      provider: str) -> dict:
        """Liquidität hinzufügen → LP-Token erhalten."""
        self._nonreentrant_enter()
        try:
            if self.lp_supply == 0:
                # Erster LP: sqrt(a * b) LP-Token
                lp_out = int(math.sqrt(amount_a * amount_b)) - DEX_CONFIG["min_liquidity"]
                if lp_out <= 0:
                    raise ValueError("Zu wenig Liquidität")
                # Min-Liquidität permanent sperren (Uniswap v2)
                self.lp_balances["LOCKED"] = DEX_CONFIG["min_liquidity"]
                self.lp_supply             = DEX_CONFIG["min_liquidity"]
            else:
                # Proportional zur bestehenden Liquidität
                lp_from_a = amount_a * self.lp_supply // self.reserve_a
                lp_from_b = amount_b * self.lp_supply // self.reserve_b
                lp_out    = min(lp_from_a, lp_from_b)

            self.reserve_a += amount_a
            self.reserve_b += amount_b
            self.lp_supply += lp_out
            self.lp_balances[provider] = self.lp_balances.get(provider, 0) + lp_out
            self.k = self._k()
            return {"lp_minted": lp_out, "reserve_a": self.reserve_a,
                    "reserve_b": self.reserve_b, "lp_supply": self.lp_supply}
        finally:
            self._nonreentrant_exit()

    def remove_liquidity(self, lp_amount: int, provider: str) -> dict:
        """LP-Token einlösen → token_a + token_b erhalten."""
        self._nonreentrant_enter()
        try:
            if self.lp_balances.get(provider, 0) < lp_amount:
                raise ValueError("Unzureichende LP-Token")
            amount_a = lp_amount * self.reserve_a // self.lp_supply
            amount_b = lp_amount * self.reserve_b // self.lp_supply
            # State VOR emit
            self.lp_balances[provider] -= lp_amount
            self.lp_supply   -= lp_amount
            self.reserve_a   -= amount_a
            self.reserve_b   -= amount_b
            self.k            = self._k()
            return {"amount_a": amount_a, "amount_b": amount_b,
                    "lp_burned": lp_amount}
        finally:
            self._nonreentrant_exit()

    def get_tvl(self, atc_price_usd: float = 0.0) -> dict:
        return {
            "reserve_a":   self.reserve_a,
            "reserve_b":   self.reserve_b,
            "lp_supply":   self.lp_supply,
            "price":       self.get_price(),
            "k":           self.k,
            "fees_earned": {"a": self.fees_earned_a, "b": self.fees_earned_b},
        }

class SwapRouter:
    """
    DEX Swap-Router — direkte + Multi-Hop Swaps.
    Findet günstigsten Pfad: ATC→FFT oder ATC→SATC→FFT
    """

    def __init__(self):
        self.pools: Dict[str, LiquidityPool] = {}

    def register_pool(self, pool: LiquidityPool):
        key = f"{pool.token_a}-{pool.token_b}"
        self.pools[key] = pool
        # Auch umgekehrt
        self.pools[f"{pool.token_b}-{pool.token_a}"] = pool

    def find_pool(self, token_in: str, token_out: str) -> Optional[LiquidityPool]:
        return self.pools.get(f"{token_in}-{token_out}")

    def get_quote(self, token_in: str, token_out: str, amount_in: int) -> dict:
        """Berechnet erwarteten Output ohne State-Änderung."""
        pool = self.find_pool(token_in, token_out)
        if not pool:
            raise ValueError(f"Kein Pool für {token_in}↔{token_out}")
        a_to_b = pool.token_a == token_in
        res_in  = pool.reserve_a if a_to_b else pool.reserve_b
        res_out = pool.reserve_b if a_to_b else pool.reserve_a
        amount_out = pool._get_amount_out(amount_in, res_in, res_out)
        impact     = pool.get_price_impact(amount_in, a_to_b)
        return {
            "token_in":     token_in, "token_out":    token_out,
            "amount_in":    amount_in, "amount_out":   amount_out,
            "price_impact": f"{impact*100:.3f}%",
            "fee":          amount_in * pool.fee_bps // 10000,
            "pool_id":      pool.pool_id,
        }

    def swap(self, token_in: str, token_out: str, amount_in: int,
             min_out: int, trader: str) -> dict:
        """Führt Swap aus."""
        pool   = self.find_pool(token_in, token_out)
        if not pool: raise ValueError(f"Kein Pool: {token_in}↔{token_out}")
        a_to_b = pool.token_a == token_in
        if a_to_b:
            return pool.swap_a_to_b(amount_in, min_out, trader)
        else:
            return pool.swap_b_to_a(amount_in, min_out, trader)
