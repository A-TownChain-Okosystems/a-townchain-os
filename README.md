# A-TownChain OS

> **Status:** v3.2.1 Released ✅ | Fortschritt: **78%** | 1 offenes Issue
> *Stand: 2026-06-14 | Aurora v3.2*

## 🚀 Quickstart

```bash
# Repository klonen
git clone https://github.com/A-TownChain-Okosystems/a-townchain-os.git
cd a-townchain-os

# Testnet starten
make -C docker testnet-up

# Health check
make -C docker health

# Tests ausführen
python -m pytest tests/ -v --tb=short
```

## 📦 Kanonische Module (v3.2.1)

| Modul | Import-Pfad | Status |
|-------|-------------|--------|
| ATCFS (VFS) | `modules.kernel.atcfs.atcfs` | ✅ Produktiv |
| AIKernel | `modules.kernel.ai_kernel.ai_kernel` | ✅ Produktiv |
| IPC Bus | `modules.kernel.ipc.ipc_bus` | ✅ Produktiv |
| ProcessManager | `modules.kernel.process.process_mgr` | ✅ Produktiv |
| P2PNode | `modules.atcnet.p2p_node` | ✅ Produktiv |
| GossipProtocol | `modules.atcnet.gossip` | ✅ Produktiv |
| ZKP Groth16 | `blockchain.zkp.groth16` | ✅ Neu |
| ATCSwap AMM | `blockchain.contracts.solidity.ATCSwap` | ✅ Neu |
| Mobile Wallet | `mobile.wallet.biometric_auth` | ✅ Neu |
| BigQuery Pipeline | `tools.bigquery_pipeline` | ✅ Neu |

## 🗺️ Roadmap

| Sprint | Version | Status |
|--------|---------|--------|
| Kernel + ATCNet | v3.2.0 | ✅ Abgeschlossen |
| Issue-Sprint | v3.2.1 | ✅ Abgeschlossen |
| CI/CD + ZKP Deep | v3.3.0 | 🔜 In Planung |
| DeFi Launch | v3.4.0 | 📋 Geplant |
| **Mainnet** | v4.0.0 | ⏳ Eckdaten fehlen |

## 🔓 Offenes Issue

| # | Titel | Blockiert durch |
|---|-------|----------------|
| [#52](../../issues/52) | Mainnet Launch Manager | Genesis-Wallet + Validator-Keys + Bootstrap-IP |

## 🏗️ Architektur

```
A-TownChain OS
├── gateway/           # API-Gateway (Port 4000)
├── blockchain/        # Core, Consensus, Contracts, ZKP
├── modules/
│   ├── kernel/        # ATCFS, AIKernel, IPC, ProcessMgr
│   └── atcnet/        # P2P, Gossip, NAT
├── atclang/           # ATCLang v0.4.0 + TypeChecker + Stdlib
├── monitoring/        # Prometheus + Grafana
├── mobile/wallet/     # BiometricAuth + FCM + WalletConnect
├── tools/             # HF-Pipeline, BigQuery
└── docker/            # Testnet Docker-Compose + Makefile
```

## 📋 Eckdaten für Mainnet (#52)

```json
{
  "chain_id":        9001,
  "token":           "ATC",
  "supply":          "21.000.000 ATC",
  "block_time":      "6000ms",
  "consensus":       "Hybrid PoW/PoS",
  "staking_reward":  "8% p.a.",
  "validator_bond":  "10.000 ATC",
  "TODO": {
    "genesis_wallet": "AUSFÜLLEN",
    "validators":     "5x Ed25519 Keys generieren",
    "bootstrap_ip":   "VPS-IP/Domain eintragen"
  }
}
```

---
*Aurora Superagent v3.2 · 2026-06-14*
