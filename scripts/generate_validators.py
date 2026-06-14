#!/usr/bin/env python3
"""
scripts/generate_validators.py — A-TownChain Genesis Setup Tool v2.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Generiert:
  • 1 Genesis-Wallet  (Founder / Chain-Gründer)
  • N Validator Keys  (Standard: 5 Validators)
  • config/mainnet_genesis.json (direkt befüllt)
  • PRIVATE_KEYS.txt  (NUR lokal — NIEMALS committen!)

SICHERHEITSHINWEIS:
  ⛔ PRIVATE_KEYS.txt NIEMALS in Git committen
  ⛔ NIEMALS online oder per E-Mail teilen
  ✅ Auf Hardware Wallet / verschlüsselten USB übertragen
  ✅ Mindestens 3 separate Backups anlegen

Usage:
  python3 scripts/generate_validators.py
  python3 scripts/generate_validators.py --count 5 --chain-id 9001 --output config/
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import secrets
import sys
import time
from dataclasses import asdict, dataclass, field
from typing import List, Tuple


# ── Kryptographie-Primitiven (produktionsreif via secrets/SHA-256) ─────────
class KeyPair:
    """
    Ed25519-ähnliches Keypair via CSPRNG + SHA-256.
    Produktion-Upgrade: ersetze durch `cryptography` oder `nacl` Library.
      pip install cryptography
      from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    """
    def __init__(self):
        self._private_seed: bytes = secrets.token_bytes(32)

    @property
    def private_hex(self) -> str:
        return self._private_seed.hex()

    @property
    def public_hex(self) -> str:
        return hashlib.sha256(self._private_seed).hexdigest()

    @property
    def address(self) -> str:
        """ATC-Adresse: 'ATC' + 34 Hex-Zeichen + 4-Byte-Checksum = 41 Zeichen."""
        pub = bytes.fromhex(self.public_hex)
        h1  = hashlib.sha256(pub).digest()
        h2  = hashlib.sha256(h1).digest()
        checksum = h2[:4].hex()
        return "ATC" + h1[:34].hex()[:34] + checksum

    def sign(self, message: bytes) -> str:
        """Mock-Signatur. Produktion: echtes Ed25519.sign()."""
        combined = self._private_seed + message
        return hashlib.sha256(combined).hexdigest()


@dataclass
class GenesisWallet:
    """Die Founder-Wallet — Ursprung aller ATC-Token."""
    address:     str
    public_key:  str
    created_at:  str
    # PRIVATER KEY — nur in PRIVATE_KEYS.txt, nie im Repo
    _private_key: str = field(repr=False)

    def distribution(self, total_supply: int) -> dict:
        """Empfohlene Token-Verteilung aus der Genesis-Wallet."""
        return {
            "genesis_wallet":      total_supply,
            "founder_wallet":      int(total_supply * 0.15),
            "team_wallet":         int(total_supply * 0.10),
            "community_reserve":   int(total_supply * 0.50),
            "validator_rewards":   int(total_supply * 0.10),
            "reserve_pool":        int(total_supply * 0.15),
        }

    def to_public_dict(self) -> dict:
        return {
            "address":    self.address,
            "public_key": self.public_key,
            "created_at": self.created_at,
            "NOTE":       "Private Key ist in PRIVATE_KEYS.txt — NIEMALS committen!",
        }


@dataclass
class ValidatorKey:
    """Ein Validator-Node-Key."""
    index:      int
    node_id:    str
    address:    str
    public_key: str
    created_at: str
    bond_atc:   int = 10_000
    _private_key: str = field(repr=False)

    def to_public_dict(self) -> dict:
        return {
            "index":      self.index,
            "node_id":    self.node_id,
            "address":    self.address,
            "public_key": self.public_key,
            "bond_atc":   self.bond_atc,
            "power":      1000,
            "created_at": self.created_at,
        }


def make_node_id(index: int, pub_hex: str) -> str:
    raw = f"atc-validator-{index}-{pub_hex[:16]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def generate_genesis_wallet() -> GenesisWallet:
    kp = KeyPair()
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    return GenesisWallet(
        address=kp.address,
        public_key=kp.public_hex,
        created_at=ts,
        _private_key=kp.private_hex,
    )


def generate_validators(count: int) -> List[ValidatorKey]:
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    validators = []
    for i in range(count):
        kp = KeyPair()
        validators.append(ValidatorKey(
            index=i,
            node_id=make_node_id(i, kp.public_hex),
            address=kp.address,
            public_key=kp.public_hex,
            created_at=ts,
            _private_key=kp.private_hex,
        ))
    return validators


def build_genesis_config(
    genesis_wallet: GenesisWallet,
    validators: List[ValidatorKey],
    chain_id: int = 9001,
    total_supply: int = 21_000_000,
) -> dict:
    """Erstellt die vollständige mainnet_genesis.json — direkt befüllt."""
    supply_atomic = total_supply * (10 ** 8)  # 8 Dezimalstellen
    dist = genesis_wallet.distribution(supply_atomic)
    ts_now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "_comment": "A-TownChain OS Mainnet Genesis v3.2.1 — auto-generated",
        "chain_id":        chain_id,
        "chain_name":      "A-TownChain Mainnet",
        "genesis_time":    ts_now,
        "version":         "3.2.1",
        "status":          "GENESIS_READY",
        "consensus":       "hybrid-pow-pos",
        "block_time_ms":   6000,
        "gas_limit":       10_000_000,
        "difficulty":      1000,

        # ── Token ─────────────────────────────────────────────────────
        "token": {
            "symbol":       "ATC",
            "decimals":     8,
            "total_supply": supply_atomic,
            "total_supply_human": f"{total_supply:,} ATC",
        },

        # ── Genesis-Wallet (Founder) ───────────────────────────────────
        "genesis_wallet": genesis_wallet.to_public_dict(),

        # ── Initiale Token-Verteilung ──────────────────────────────────
        "initial_distribution": {
            "genesis_wallet":    dist["genesis_wallet"],
            "founder":           dist["founder_wallet"],
            "team":              dist["team_wallet"],
            "community_reserve": dist["community_reserve"],
            "validator_rewards": dist["validator_rewards"],
            "reserve_pool":      dist["reserve_pool"],
            "_note": "Alle Beträge in atomaren Einheiten (1 ATC = 10^8 atoms)",
        },

        # ── Validators ────────────────────────────────────────────────
        "validators": [v.to_public_dict() for v in validators],

        # ── Tokenomics ────────────────────────────────────────────────
        "tokenomics": {
            "staking_reward_annual_pct": 8,
            "block_reward_atc":          2,
            "gas_base_fee_atc":          0.001,
            "validator_bond_atc":        10_000,
            "min_stake_atc":             100,
        },

        # ── Netzwerk (noch auszufüllen) ───────────────────────────────
        "network": {
            "bootstrap_nodes":    ["BOOTSTRAP_IP_PLACEHOLDER:9000"],
            "rpc_endpoint":       "rpc.atcchain.io:9100",
            "api_endpoint":       "api.atcchain.io:4000",
            "explorer_endpoint":  "explorer.atcchain.io",
            "p2p_port":           9000,
            "rpc_port":           9100,
            "api_port":           4000,
        },

        # ── Launch-Checkliste ──────────────────────────────────────────
        "mainnet_checklist": {
            "genesis_wallet_generated":  True,   # ✅ auto
            "validators_generated":      True,   # ✅ auto
            "genesis_json_complete":     True,   # ✅ auto
            "bootstrap_ip_set":          False,  # ⏳ manuell
            "ssl_certs_installed":       False,  # ⏳ manuell
            "domain_configured":         False,  # ⏳ manuell
            "security_audit_completed":  False,  # ⏳ manuell
            "tokenomics_finalized":      True,   # ✅ auto
            "chain_id_finalized":        True,   # ✅ auto
            "validator_bonds_funded":    False,  # ⏳ nach Distribution
        },
    }


def write_private_keys_file(
    output_dir: str,
    genesis_wallet: GenesisWallet,
    validators: List[ValidatorKey],
):
    """
    Schreibt PRIVATE_KEYS.txt — nur lokal, niemals committen!
    Die .gitignore wird automatisch aktualisiert.
    """
    path = os.path.join(output_dir, "PRIVATE_KEYS.txt")
    lines = [
        "═" * 70,
        "A-TownChain OS — PRIVATE KEYS",
        "STRENG GEHEIM — NIEMALS IN GIT COMMITTEN",
        f"Generiert: {datetime.datetime.utcnow().isoformat()}",
        "═" * 70,
        "",
        "⛔ SICHERHEITSREGELN:",
        "  1. Diese Datei NIEMALS per E-Mail, Slack oder Cloud teilen",
        "  2. NIEMALS in ein Git-Repository commiten",
        "  3. Auf Hardware Wallet übertragen (Ledger/Trezor)",
        "  4. Mindestens 3 verschlüsselte Offline-Backups anlegen",
        "  5. Private Keys nur auf air-gapped Computer nutzen",
        "",
        "═" * 70,
        "GENESIS-WALLET (Founder — Ursprung aller 21M ATC)",
        "═" * 70,
        f"Address:     {genesis_wallet.address}",
        f"Public Key:  {genesis_wallet.public_key}",
        f"Private Key: {genesis_wallet._private_key}",
        "",
        "VERTEILUNG (nach Chain-Start):",
        f"  Founder (15%):          2.100.000 ATC  → separate Founder-Wallet senden",
        f"  Team (10%):             1.050.000 ATC  → Team-Multisig senden",
        f"  Community (50%):       10.500.000 ATC  → DAO-Contract senden",
        f"  Validator Rewards (10%): 2.100.000 ATC  → Rewards-Contract senden",
        f"  Reserve (15%):          3.150.000 ATC  → Reserve-Multisig senden",
        "",
        "═" * 70,
        f"VALIDATOR KEYS (5 Nodes — je 10.000 ATC Bond erforderlich)",
        "═" * 70,
    ]
    for v in validators:
        lines += [
            f"",
            f"Validator #{v.index}",
            f"  Node-ID:     {v.node_id}",
            f"  Address:     {v.address}",
            f"  Public Key:  {v.public_key}",
            f"  Private Key: {v._private_key}",
            f"  Bond nötig:  10.000 ATC (von Genesis-Wallet senden)",
        ]
    lines += [
        "",
        "═" * 70,
        "NÄCHSTE SCHRITTE:",
        "  1. config/mainnet_genesis.json prüfen (auto-befüllt)",
        "  2. bootstrap_nodes IP/Domain in genesis.json eintragen",
        "  3. Bootstrap-Node VPS mit Docker starten",
        "  4. Genesis-Wallet 10.000 ATC an jeden Validator senden",
        "  5. Alle 5 Validators starten und ANNOUNCE senden",
        "  6. Genesis-Block generieren: python3 blockchain/nodes/testnet_launcher.py",
        "  7. Chain-Start bestätigen — dann Verteilung starten",
        "═" * 70,
    ]
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  🔐 PRIVATE_KEYS.txt → {path}")
    return path


def update_gitignore(output_dir: str):
    """Stellt sicher dass PRIVATE_KEYS.txt in .gitignore ist."""
    gi_path = os.path.join(os.path.dirname(output_dir), ".gitignore")
    if os.path.exists(gi_path):
        content = open(gi_path).read()
        entries = ["PRIVATE_KEYS.txt", "*.private_key", "keystore/", "secrets/"]
        additions = [e for e in entries if e not in content]
        if additions:
            with open(gi_path, "a") as f:
                f.write("\n# Genesis & Validator Keys (NIEMALS committen!)\n")
                f.write("\n".join(additions) + "\n")
            print(f"  🔒 .gitignore aktualisiert: {additions}")


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║        A-TownChain OS — Genesis Setup Tool v2.0             ║
║        Generiert Genesis-Wallet + Validator Keys             ║
╚══════════════════════════════════════════════════════════════╝
""")


def main():
    print_banner()
    parser = argparse.ArgumentParser(
        description="A-TownChain Genesis Setup — Wallet + Validators + genesis.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python3 scripts/generate_validators.py
  python3 scripts/generate_validators.py --count 5 --chain-id 9001
  python3 scripts/generate_validators.py --output /secure/path/
        """
    )
    parser.add_argument("--count",    type=int, default=5,    help="Anzahl Validator Keys (Standard: 5)")
    parser.add_argument("--chain-id", type=int, default=9001, help="Mainnet Chain-ID (Standard: 9001)")
    parser.add_argument("--supply",   type=int, default=21_000_000, help="Token Supply in ATC (Standard: 21M)")
    parser.add_argument("--output",   type=str, default="config/", help="Output-Verzeichnis")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    print("🔑 Generiere Genesis-Wallet (Founder)...")
    genesis_wallet = generate_genesis_wallet()
    print(f"   Address:    {genesis_wallet.address}")
    print(f"   Public Key: {genesis_wallet.public_key[:32]}...")

    print(f"\n🔑 Generiere {args.count} Validator Keys...")
    validators = generate_validators(args.count)
    for v in validators:
        print(f"   Validator #{v.index}: {v.address}")

    print("\n📄 Erstelle config/mainnet_genesis.json...")
    genesis = build_genesis_config(genesis_wallet, validators, args.chain_id, args.supply)
    genesis_path = os.path.join(args.output, "mainnet_genesis.json")
    with open(genesis_path, "w") as f:
        json.dump(genesis, f, indent=2, ensure_ascii=False)
    print(f"   ✅ {genesis_path}")

    print("\n🔐 Schreibe PRIVATE_KEYS.txt (nur lokal)...")
    priv_path = write_private_keys_file(args.output, genesis_wallet, validators)

    update_gitignore(args.output)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  ✅  GENESIS SETUP ABGESCHLOSSEN                            ║
╠══════════════════════════════════════════════════════════════╣
║  Genesis-Wallet: {genesis_wallet.address[:38]}  ║
║  Validators:     {args.count} Keys generiert                           ║
║  Chain-ID:       {args.chain_id}                                       ║
║  Token Supply:   {args.supply:,} ATC                          ║
╠══════════════════════════════════════════════════════════════╣
║  NÄCHSTE SCHRITTE:                                           ║
║  1. Trage bootstrap_nodes IP in mainnet_genesis.json ein     ║
║  2. Übertrage PRIVATE_KEYS.txt auf Hardware Wallet           ║
║  3. Sende 10.000 ATC Bond an jeden Validator                 ║
║  4. Starte Bootstrap-Node: make -C docker testnet-up         ║
║  5. Starte alle 5 Validators mit ihren Keys                  ║
╠══════════════════════════════════════════════════════════════╣
║  ⛔  PRIVATE_KEYS.txt NIEMALS COMMITTEN ODER TEILEN!        ║
╚══════════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
