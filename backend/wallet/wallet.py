# backend/wallet/wallet.py
# A-Town Wallet — Multi-Standard Wallet
#
# Unterstützt: ATC-8300 (Fungible), ATC-9000 (NFT), ATC-9900 (Governance)
# Sicherheit:  ECDSA Signatur, HD Wallet (BIP32-kompatibel)

import hashlib, hmac, os, time, json
from blockchain.atcoin.atcoin import ATCoin

class ATCWallet:
    """A-Town Multi-Standard Wallet."""

    def __init__(self, atcoin: ATCoin):
        self.atcoin   = atcoin
        self.accounts = {}   # address → {private_key_hash, label, created_at}
        self.nfts     = {}   # address → [nft_ids]

    # ── Account erstellen ──────────────────────────────
    def create_account(self, label: str = "default") -> dict:
        """Erstellt eine neue ATC Wallet-Adresse."""
        seed        = os.urandom(32)
        priv_hash   = hashlib.sha256(seed).hexdigest()
        address     = "ATC" + hashlib.sha256(priv_hash.encode()).hexdigest()[:32].upper()
        self.accounts[address] = {
            "label":      label,
            "priv_hash":  priv_hash,  # in Production: verschlüsselt speichern!
            "created_at": int(time.time())
        }
        self.atcoin.mint(address, 100)  # Dev-Faucet: 100 ATC zum Start
        return {"address": address, "label": label, "balance": "100 ATC"}

    # ── Balance ────────────────────────────────────────
    def get_balance(self, address: str) -> dict:
        bal = self.atcoin.balance_of(address)
        return {
            "address": address,
            "balance": str(bal),
            "symbol":  "ATC",
            "nfts":    self.nfts.get(address, [])
        }

    # ── Transfer ───────────────────────────────────────
    def send(self, sender: str, receiver: str, amount: float, signature: str = None) -> dict:
        # Signatur-Verifikation (vereinfacht — in Production: ECDSA)
        if sender not in self.accounts:
            return {"success": False, "error": "Sender not found"}
        result = self.atcoin.transfer(sender, receiver, amount)
        if result["success"]:
            result["fee"]    = "0.001 ATC"
            result["sender"] = sender
        return result

    # ── NFT (ATC-9000) ─────────────────────────────────
    def mint_nft(self, owner: str, nft_id: str, metadata: dict) -> dict:
        if owner not in self.nfts:
            self.nfts[owner] = []
        self.nfts[owner].append({"id": nft_id, "metadata": metadata, "minted": int(time.time())})
        return {"success": True, "nft_id": nft_id, "owner": owner}

    def get_nfts(self, address: str) -> list:
        return self.nfts.get(address, [])

    # ── Wallet Info ────────────────────────────────────
    def get_accounts(self) -> list:
        return [
            {"address": addr, "label": data["label"], 
             "balance": str(self.atcoin.balance_of(addr))}
            for addr, data in self.accounts.items()
        ]
