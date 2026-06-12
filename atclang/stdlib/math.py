"""
ATCLang Stdlib — ATC::Math
Safe integer arithmetic for smart contracts.
Issue: #48 | Wiki: Kap. 36
"""
import math as _math
from typing import Union

Num = Union[int, float]


class ATCMath:
    """
    ATC::Math — Safe arithmetic for ATCLang contracts.
    All operations check for overflow and division-by-zero.
    """
    MAX_U64 = (1 << 64) - 1
    MAX_U32 = (1 << 32) - 1

    @staticmethod
    def add(a: int, b: int) -> int:
        result = a + b
        if result > ATCMath.MAX_U64:
            raise OverflowError(f"add overflow: {a} + {b}")
        return result

    @staticmethod
    def sub(a: int, b: int) -> int:
        if b > a:
            raise ArithmeticError(f"sub underflow: {a} - {b}")
        return a - b

    @staticmethod
    def mul(a: int, b: int) -> int:
        result = a * b
        if result > ATCMath.MAX_U64:
            raise OverflowError(f"mul overflow: {a} * {b}")
        return result

    @staticmethod
    def div(a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("ATC::Math.div by zero")
        return a // b

    @staticmethod
    def mod(a: int, b: int) -> int:
        if b == 0:
            raise ZeroDivisionError("ATC::Math.mod by zero")
        return a % b

    @staticmethod
    def pow(base: int, exp: int) -> int:
        result = base ** exp
        if result > ATCMath.MAX_U64:
            raise OverflowError(f"pow overflow: {base}^{exp}")
        return result

    @staticmethod
    def sqrt(x: int) -> int:
        if x < 0:
            raise ValueError("sqrt of negative")
        return int(_math.isqrt(x))

    @staticmethod
    def min(a: int, b: int) -> int:
        return a if a < b else b

    @staticmethod
    def max(a: int, b: int) -> int:
        return a if a > b else b

    @staticmethod
    def clamp(value: int, lo: int, hi: int) -> int:
        return ATCMath.max(lo, ATCMath.min(value, hi))

    @staticmethod
    def percentage(amount: int, bps: int) -> int:
        """Calculate percentage using basis points (100 bps = 1%)."""
        return ATCMath.div(ATCMath.mul(amount, bps), 10000)

    @staticmethod
    def is_power_of_two(n: int) -> bool:
        return n > 0 and (n & (n - 1)) == 0
