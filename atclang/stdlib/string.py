"""ATCLang Stdlib — ATC::String"""
import re

class ATCString:
    @staticmethod
    def concat(*parts: str) -> str:
        return "".join(str(p) for p in parts)

    @staticmethod
    def length(s: str) -> int:
        return len(s)

    @staticmethod
    def slice(s: str, start: int, end: int) -> str:
        return s[start:end]

    @staticmethod
    def to_lower(s: str) -> str:
        return s.lower()

    @staticmethod
    def to_upper(s: str) -> str:
        return s.upper()

    @staticmethod
    def contains(s: str, sub: str) -> bool:
        return sub in s

    @staticmethod
    def split(s: str, sep: str) -> list:
        return s.split(sep)

    @staticmethod
    def trim(s: str) -> str:
        return s.strip()

    @staticmethod
    def replace(s: str, old: str, new: str) -> str:
        return s.replace(old, new)
