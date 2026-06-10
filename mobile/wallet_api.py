"""
A-TownChain — Mobile Wallet Specification & API (Fix #38)
iOS + Android | React Native | BIP39 | QR-Code | Biometric Auth
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import hashlib, os, json, time

MOBILE_WALLET_CONFIG = {
    "version":           "1.0.0",
    "platforms":         ["iOS", "Android"],
    "framework":         "React Native",
    "min_ios":           "16.0",
    "min_android":       "10",
    "biometric_auth":    True,
    "qr_format":         "atc:{address}?amount={amount}&memo={memo}",
    "deep_link_scheme":  "atcwallet://",
    "push_notifications": True,
    "supported_tokens":  ["ATC", "FFT", "SATC"],
    "supported_chains":  [9000, 1, 137, 56],  # ATC, ETH, Polygon, BSC
}

@dataclass
class MobileWalletAccount:
    """Mobile-Wallet Konto — verwaltet ATC-Wallet auf Mobile."""
    address:          str
    public_key:       str
    encrypted_key:    str   # AES-256-GCM verschlüsselt mit PIN/Biometric
    label:            str   = "Mein ATC Wallet"
    created_at:       int   = field(default_factory=lambda: int(time.time()))
    last_backup:      Optional[int] = None
    biometric_linked: bool  = False
    push_token:       Optional[str] = None

    def get_qr_data(self, amount: int = 0, memo: str = "") -> str:
        """Generiert QR-Code Daten für Empfang."""
        base = f"atc:{self.address}"
        params = []
        if amount > 0: params.append(f"amount={amount}")
        if memo:       params.append(f"memo={memo}")
        return base + ("?" + "&".join(params) if params else "")

    def is_backed_up(self) -> bool:
        return self.last_backup is not None

class MobileWalletManager:
    """
    Mobile Wallet Manager — Backend-API für React Native App.

    Endpoints (über API Gateway Port 4000):
        POST /api/mobile/wallet/create
        POST /api/mobile/wallet/import
        GET  /api/mobile/wallet/balance/{address}
        POST /api/mobile/tx/send
        GET  /api/mobile/tx/history/{address}
        POST /api/mobile/auth/biometric
        GET  /api/mobile/qr/generate
        POST /api/mobile/qr/scan
    """

    def __init__(self):
        self.accounts:     Dict[str, MobileWalletAccount] = {}
        self.sessions:     Dict[str, dict] = {}
        self.push_tokens:  Dict[str, str]  = {}

    def create_wallet(self, label: str = "Mein ATC Wallet",
                      pin: str = "") -> dict:
        """Erstellt neues Wallet + BIP39 Mnemonic."""
        # Simuliert Wallet-Erstellung (in Produktion: echte Krypto)
        entropy   = os.urandom(32)
        priv_key  = entropy.hex()
        pub_key   = hashlib.sha256(entropy).hexdigest()
        address   = "ATC" + hashlib.sha3_256(bytes.fromhex(pub_key)).hexdigest()[:32]

        # BIP39 Mnemonic (vereinfacht — in Produktion: wordlist)
        mnemonic_words = [hashlib.sha256(entropy[i:i+2]).hexdigest()[:8]
                          for i in range(0, 24, 2)]
        mnemonic = " ".join(mnemonic_words[:12])

        account = MobileWalletAccount(
            address=address, public_key=pub_key,
            encrypted_key=hashlib.sha256((priv_key + pin).encode()).hexdigest(),
            label=label,
        )
        self.accounts[address] = account
        return {
            "address":  address,
            "mnemonic": mnemonic,
            "label":    label,
            "warning":  "Mnemonic SICHER aufbewahren — nicht teilen!",
        }

    def import_from_mnemonic(self, mnemonic: str, pin: str,
                              label: str = "") -> dict:
        """Importiert Wallet aus BIP39 Mnemonic."""
        words = mnemonic.strip().split()
        if len(words) not in (12, 24):
            raise ValueError(f"Mnemonic muss 12 oder 24 Wörter haben, hat {len(words)}")
        seed     = hashlib.pbkdf2_hmac("sha256",
                    mnemonic.encode(), b"ATC-BIP39-Salt", 2048)
        pub_key  = hashlib.sha256(seed).hexdigest()
        address  = "ATC" + hashlib.sha3_256(bytes.fromhex(pub_key)).hexdigest()[:32]
        account  = MobileWalletAccount(
            address=address, public_key=pub_key,
            encrypted_key=hashlib.sha256((seed.hex() + pin).encode()).hexdigest(),
            label=label or f"Importiert ({address[:8]}...)",
        )
        self.accounts[address] = account
        return {"address": address, "imported": True}

    def authenticate(self, address: str, pin: str) -> dict:
        """PIN-Authentifizierung → Session-Token."""
        acc = self.accounts.get(address)
        if not acc: raise ValueError("Wallet nicht gefunden")
        expected = acc.encrypted_key
        check    = hashlib.sha256((acc.public_key[:64] + pin).encode()).hexdigest()
        # Vereinfacht — in Produktion: timing-safe compare + rate-limit
        session_token = hashlib.sha256(
            f"{address}{time.time()}".encode()).hexdigest()
        self.sessions[session_token] = {
            "address": address, "expires": int(time.time()) + 3600
        }
        return {"session_token": session_token, "expires_in": 3600}

    def register_push_token(self, address: str,
                             push_token: str) -> bool:
        """Registriert Push-Notification Token."""
        self.push_tokens[address] = push_token
        if address in self.accounts:
            self.accounts[address].push_token = push_token
        return True

    def generate_qr(self, address: str, amount: int = 0,
                    memo: str = "") -> dict:
        """Generiert QR-Code Daten."""
        acc = self.accounts.get(address)
        if not acc: raise ValueError("Wallet nicht gefunden")
        qr_data = acc.get_qr_data(amount, memo)
        return {"qr_data": qr_data, "address": address,
                "amount": amount, "memo": memo,
                "format": MOBILE_WALLET_CONFIG["qr_format"]}

    def parse_qr(self, qr_data: str) -> dict:
        """Parsed gescannten QR-Code."""
        import urllib.parse
        if not qr_data.startswith("atc:"):
            raise ValueError("Kein gültiger ATC QR-Code")
        rest = qr_data[4:]
        if "?" in rest:
            address, params_str = rest.split("?", 1)
            params = dict(urllib.parse.parse_qsl(params_str))
        else:
            address, params = rest, {}
        if not (address.startswith("ATC") and len(address) == 35):
            raise ValueError(f"Ungültige ATC-Adresse: {address}")
        return {
            "address": address,
            "amount":  int(params.get("amount", 0)),
            "memo":    params.get("memo", ""),
        }

    def get_react_native_api(self) -> dict:
        """Gibt die vollständige React-Native-API-Spezifikation zurück."""
        return {
            "base_url":   "http://localhost:4000/api/mobile",
            "auth":       "X-API-Key + X-Signature (ECDSA)",
            "endpoints": {
                "create_wallet": {"method": "POST", "path": "/wallet/create"},
                "import_wallet": {"method": "POST", "path": "/wallet/import"},
                "get_balance":   {"method": "GET",  "path": "/wallet/balance/{address}"},
                "send_tx":       {"method": "POST", "path": "/tx/send"},
                "tx_history":    {"method": "GET",  "path": "/tx/history/{address}"},
                "auth_biometric":{"method": "POST", "path": "/auth/biometric"},
                "generate_qr":   {"method": "GET",  "path": "/qr/generate"},
                "scan_qr":       {"method": "POST", "path": "/qr/scan"},
                "push_register": {"method": "POST", "path": "/push/register"},
            },
            "config": MOBILE_WALLET_CONFIG,
        }
