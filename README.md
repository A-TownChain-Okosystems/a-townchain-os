# ⚙️ A-TownChain OS — Software v2.0.0

> **KAI-OS v2.0 | AI-Blockchain Operating System | 13-Layer Architecture**
> Ausführbarer Quellcode aller Systemkomponenten.

[![Python](https://img.shields.io/badge/Python-75%25-blue)](modules/)
[![ATCLang](https://img.shields.io/badge/ATCLang-v0.3.0-purple)](modules/atclang/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green)](LICENSE)
[![Issues](https://img.shields.io/badge/Open_Issues-8-orange)](https://github.com/A-TownChain-Okosystems/a-townchain-os/issues)

📖 **Dokumentation & Wiki:** [a-townchain-os-docs](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs)

---

## 📦 Struktur

```
a-townchain-os/
│
├── modules/                  ← Eigenständige Module (je ein Package)
│   ├── kernel/               ← L2: ShivaOS Microkernel (IPC, ATCFS, Consensus, Net)
│   ├── gateway/              ← L7: API Gateway :4000 (Auth, Rate-Limit, Router)
│   ├── contracts/            ← L6: Smart Contracts (ATC-8300, Governance, Bridge)
│   ├── atclang/              ← L1: ATCLang Compiler + VM + REPL + Stdlib
│   ├── atcnet/               ← L5: P2P Netzwerk (Kademlia DHT, Bootstrap, Sync)
│   ├── ui/                   ← L10: Neon Dashboard (HTML/JS/CSS)
│   ├── shivamon/             ← L12: NFT Gaming Engine (Battle, Breeding)
│   ├── franchise/            ← L8: Business DAO (Vault, Revenue, Token)
│   └── standards/            ← L0: ATC/ATS Protokoll-Standards
│
├── core/                     ← Shared Services (AI-Kernel, Event-Bus, Module-Loader)
├── backend/                  ← API-Server, Orchestrator, DB, Wallet
├── blockchain/               ← Consensus (PoH/PoS/PoW), Nodes, Wallet, Contracts
├── frontend/                 ← ShivaOS Dashboard (HTML/JS/CSS)
├── tests/                    ← Alle Tests (unit/, integration/, e2e/)
├── docker/                   ← Dockerfiles pro Service
├── docker-compose.yml        ← 5-Node Testnetz (Issue #18)
├── monitoring/               ← Prometheus Config (Issue #19)
├── config/                   ← Zentrale Konfiguration
├── build/                    ← Build-System EXE/AppImage (Issue #7)
└── tools/                    ← Hilfsskripte
```

## 🚀 Schnellstart

```bash
# Abhängigkeiten
pip install -r requirements.txt

# Gesamtsystem starten
python start.py

# Einzelne Module
python -m modules.gateway.main        # API Gateway :4000
python -m modules.atclang.repl.repl   # ATCLang REPL
python -m modules.kernel.kernel       # ShivaOS Kernel

# Tests
python -m pytest tests/

# Testnet (Docker)
docker-compose up
```

## 🗺️ 13-Layer Architektur

| Layer | Modul | Status |
|-------|-------|--------|
| L0 Security Standards | modules/standards/ | ✅ |
| L1 ATCLang | modules/atclang/ | ✅ v0.3.0 |
| L2 ShivaOS Kernel | modules/kernel/ | ✅ |
| L3 AI-Kernel | core/ai_kernel.py | ✅ |
| L4 Proof of History | blockchain/consensus/ | ✅ |
| L5 ATCNet P2P | modules/atcnet/ | ✅ |
| L6 Smart Contracts | modules/contracts/ | ✅ |
| L7 API Gateway | modules/gateway/ | ✅ |
| L8 Franchise DAO | modules/franchise/ | 📋 |
| L9 Agent Registry | backend/api/ | ✅ |
| L10 Dashboard UI | modules/ui/ | ✅ |
| L11 DeFi Bridge | modules/contracts/bridge/ | 📋 |
| L12 Shivamon NFT | modules/shivamon/ | 📋 |

## 🔗 Links

| | |
|---|---|
| 📖 Dokumentation | [a-townchain-os-docs](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs) |
| 📋 Roadmap | [Notion](https://www.notion.so/373b826db85c8125ba83f04995191bf0) |
| 📊 Dashboard | [Google Sheets](https://docs.google.com/spreadsheets/d/1xR5c24NrtYC58OsGrLaUHkQUiL_O6eYVyx8KmFcvBD4) |

---
*Apache 2.0 | A-TownChain-Okosystems*


## Quickstart

```bash
git clone https://github.com/A-TownChain-Okosystems/a-townchain-os.git
cd a-townchain-os
pip install -r requirements.txt
python3 blockchain/nodes/bootstrap.py
```

Docker (empfohlen):

```bash
docker compose up -d
# Gateway: http://localhost:4000
```
