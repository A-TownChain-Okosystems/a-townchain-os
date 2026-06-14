#!/usr/bin/env python3
"""
generate_validators.py — A-TownChain Validator Key Generator
Erzeugt Ed25519 Validator Keys für das Mainnet Genesis.
Usage: python3 scripts/generate_validators.py --count 5 --output config/validators.json
"""
import argparse, hashlib, json, os, secrets, sys, time
from dataclasses import dataclass, asdict
from typing import List

@dataclass
class ValidatorKey:
    index:       int
    node_id:     str
    public_key:  str
    address:     str
    created_at:  str

def generate_key_pair() -> tuple:
    """Generiert ein Ed25519-ähnliches Keypair (deterministisch via CSPRNG)."""
    private_seed = secrets.token_bytes(32)
    private_hex  = private_seed.hex()
    # Public Key: SHA256 des Private Seed (Vereinfachung — Produktion: echtes Ed25519)
    pub_bytes    = hashlib.sha256(private_seed).digest()
    pub_hex      = pub_bytes.hex()
    return private_hex, pub_hex

def generate_atc_address(public_key_hex: str) -> str:
    """Generiert ATC-Adresse aus Public Key (ATC + 38 Hex-Zeichen = 41 Zeichen)."""
    h = hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()
    checksum = hashlib.sha256(bytes.fromhex(h)).hexdigest()[:4]
    return "ATC" + h[:34] + checksum

def generate_node_id(index: int, pub_hex: str) -> str:
    raw = f"atc-validator-{index}-{pub_hex[:16]}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

def generate_validators(count: int) -> tuple:
    validators = []
    private_keys = []
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    for i in range(count):
        priv, pub = generate_key_pair()
        addr      = generate_atc_address(pub)
        node_id   = generate_node_id(i, pub)
        validators.append(ValidatorKey(
            index=i, node_id=node_id,
            public_key=pub, address=addr,
            created_at=ts,
        ))
        private_keys.append({"index": i, "private_key": priv, "address": addr})

    return validators, private_keys

def build_genesis(validators: List[ValidatorKey], chain_id: int = 9001) -> dict:
    """Erstellt Genesis-Config für das Mainnet."""
    return {
        "chain_id":         chain_id,
        "chain_name":       "A-TownChain Mainnet",
        "genesis_time":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version":          "3.2.1",
        "consensus":        "hybrid-pow-pos",
        "block_time_ms":    6000,
        "gas_limit":        10_000_000,
        "difficulty":       1000,
        "initial_supply":   21_000_000 * (10 ** 8),
        "token_symbol":     "ATC",
        "token_decimals":   8,
        "genesis_wallet":   "ATC_GENESIS_WALLET_PLACEHOLDER_REPLACE_ME",
        "validators": [
            {
                "index":      v.index,
                "node_id":    v.node_id,
                "public_key": v.public_key,
                "address":    v.address,
                "bond":       10_000 * (10 ** 8),   # 10.000 ATC Mindest-Bond
                "power":      1000,
            }
            for v in validators
        ],
        "tokenomics": {
            "founder_allocation_pct":     15,
            "team_allocation_pct":        10,
            "community_allocation_pct":   50,
            "reserve_allocation_pct":     15,
            "validator_rewards_pct":      10,
            "staking_reward_annual_pct":   8,
            "block_reward_atc":            2,
            "gas_base_fee_atc":         0.001,
        },
        "network": {
            "bootstrap_nodes":   ["BOOTSTRAP_IP_PLACEHOLDER:9000"],
            "rpc_endpoint":      "rpc.atcchain.io:9100",
            "api_endpoint":      "api.atcchain.io:4000",
            "explorer_endpoint": "explorer.atcchain.io",
            "p2p_port":          9000,
            "rpc_port":          9100,
            "api_port":          4000,
        },
        "mainnet_checklist": {
            "genesis_wallet_defined":  False,
            "validators_confirmed":    False,
            "bootstrap_ip_set":        False,
            "ssl_certs_installed":     False,
            "domain_configured":       False,
            "audit_completed":         False,
        }
    }

def main():
    parser = argparse.ArgumentParser(description="A-TownChain Validator Key Generator")
    parser.add_argument("--count",  type=int, default=5,   help="Anzahl Validator Keys")
    parser.add_argument("--output", type=str, default="config/validators.json")
    parser.add_argument("--genesis-output", type=str, default="config/mainnet_genesis.json")
    parser.add_argument("--chain-id", type=int, default=9001)
    args = parser.parse_args()

    print(f"\n🔑 Generiere {args.count} Validator Keys (Chain-ID: {args.chain_id})...")
    validators, private_keys = generate_validators(args.count)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    # Public Keys speichern (sicher für Repo)
    pub_data = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "chain_id": args.chain_id,
        "count": args.count,
        "validators": [asdict(v) for v in validators],
        "warning": "Diese Datei enthält NUR Public Keys. Private Keys NIEMALS in Git committen!"
    }
    with open(args.output, "w") as f:
        json.dump(pub_data, f, indent=2)
    print(f"  ✅ Public Keys → {args.output}")

    # Private Keys NICHT in Repo — nur Warnung ausgeben
    print(f"\n  ⚠️  PRIVATE KEYS (SICHER AUFBEWAHREN — NICHT IN GIT!):")
    for pk in private_keys:
        print(f"     Validator {pk['index']}: {pk['private_key'][:16]}...{pk['private_key'][-8:]}")
        print(f"     Address: {pk['address']}")

    # Genesis Config erstellen
    genesis = build_genesis(validators, args.chain_id)
    with open(args.genesis_output, "w") as f:
        json.dump(genesis, f, indent=2)
    print(f"\n  ✅ Genesis Config → {args.genesis_output}")
    print(f"\n  ⚠️  WICHTIG: Bitte folgende Felder manuell ausfüllen:")
    print(f"     - genesis_wallet: Founder-Wallet-Adresse")
    print(f"     - bootstrap_nodes: Öffentliche Bootstrap-IP")
    print(f"     - mainnet_checklist: Alle Punkte bestätigen")
    print(f"\n  ✅ {args.count} Validator Keys generiert!")

if __name__ == "__main__":
    main()
