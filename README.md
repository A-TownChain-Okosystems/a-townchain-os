# 🌐 A-TownChain OS — Monorepo v3.0.0

> **KAI-OS v2.0.0 | AI-Blockchain Operating System | 13-Layer NFT Architecture**
> Alle Module, Dokumentation und Tools in einem einzigen Repository.

[![Python](https://img.shields.io/badge/Python-75%25-blue)](modules/)
[![ATCLang](https://img.shields.io/badge/ATCLang-v0.3.0-purple)](modules/atclang/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green)](LICENSE)
[![Issues](https://img.shields.io/badge/Open_Issues-8-orange)](https://github.com/A-TownChain-Okosystems/a-townchain-os/issues)

---

## 📦 Monorepo-Struktur

```
a-townchain-os/
│
├── modules/                    ← Ausführbare Module (je ein eigenständiges Package)
│   ├── kernel/                 ← L2: ShivaOS Microkernel (IPC, ATCFS, Consensus, Net)
│   ├── gateway/                ← L7: API Gateway :4000 (Auth, Rate-Limit, Router)
│   ├── contracts/              ← L6: Smart Contracts (ATC-8300, Governance, Bridge)
│   ├── atclang/                ← L1: ATCLang Compiler + VM + REPL + Stdlib
│   ├── atcnet/                 ← L5: P2P Netzwerk (Kademlia DHT, Bootstrap, Sync)
│   ├── ui/                     ← L10: Neon Dashboard (HTML/JS/CSS)
│   ├── shivamon/               ← L12: NFT Gaming Engine (Battle, Breeding)
│   ├── franchise/              ← L8: Business DAO (Vault, Revenue, Token)
│   └── standards/              ← L0: ATC/ATS Protokoll-Standards
│
├── core/                       ← Shared Kernel-Services
│   ├── ai_kernel.py            ← L3: KI-Modul (Orchestrator)
│   ├── event_bus.py            ← Event-System
│   ├── module_loader.py        ← Dynamisches Modul-Loading
│   └── kernel.py               ← Master-Kernel-Entry
│
├── backend/                    ← API-Server & Datenbank
│   ├── api/                    ← REST-Routen (Wallet, Blockchain, AI, Game)
│   ├── db/                     ← Repository Pattern + Schema
│   └── wallet/                 ← Backend-Wallet-Service
│
├── blockchain/                 ← Chain & Consensus
│   ├── consensus/              ← Hybrid PoH + PoS + PoW
│   ├── contracts/              ← On-Chain Contracts
│   ├── nodes/                  ← Node Discovery + P2P Propagation
│   └── wallet/                 ← ECDSA Keygen + Signing
│
├── frontend/                   ← ShivaOS Dashboard
│   ├── index.html              ← Neon UI Entry Point
│   ├── assets/                 ← JS + CSS
│   ├── battle/                 ← Shivamon Battle UI
│   └── bootscreen/             ← Boot-Animation
│
├── tests/                      ← Zentrales Test-Verzeichnis
│   ├── unit/                   ← Unit Tests (atclang, ecdsa, gateway, p2p...)
│   ├── integration/            ← Integration Tests
│   └── e2e/                    ← End-to-End Tests (Testnet)
│
├── docs/                       ← Gesamte Dokumentation
│   ├── whitepaper/             ← Offizielles Whitepaper v2.1.0
│   ├── architecture/           ← Architektur-Doku (Kernel, Gateway, Consensus...)
│   ├── standards/              ← ATC-0001–0009 + ATS-1000–1009
│   ├── ai/                     ← AI Safety, LLM Router, Gemini Integration
│   ├── roadmap/                ← Sprints, Meilensteine, Issue-Tracking
│   └── wiki/                   ← Modul-spezifische Wiki-Seiten
│       ├── kai-os/             ← KAI-OS Theorie & 31-Kapitel-Architektur
│       ├── kernel/             ← Kernel-Dokumentation
│       ├── gateway/            ← Gateway-Routen & Middleware
│       ├── contracts/          ← Smart Contract API
│       ├── atclang/            ← ATCLang Sprachspezifikation
│       ├── atcnet/             ← P2P Protokoll & Topologie
│       ├── ui/                 ← Frontend-Architektur
│       ├── shivamon/           ← Game-Engine & NFT-Spezifikation
│       ├── franchise/          ← Franchise DAO Konzept
│       └── standards/          ← Standards-Wiki
│
├── docker/                     ← Docker & Testnet
│   └── docker-compose.yml      ← 5-Node lokales Testnetz (Issue #18)
├── config/                     ← Zentrale Konfiguration
├── monitoring/                 ← Node-Monitoring (Issue #19)
└── tools/                      ← Build-Tools & Scripts
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

# Tests ausführen
python -m pytest tests/unit/

# Testnet (Docker) — Issue #18
docker-compose up
```

## 🗺️ 13-Layer Architektur

| Layer | Name | Modul | Status |
|-------|------|-------|--------|
| L0 | Security Standards | modules/standards/ | ✅ |
| L1 | ATCLang | modules/atclang/ | ✅ v0.3.0 |
| L2 | ShivaOS Kernel | modules/kernel/ | ✅ |
| L3 | AI-Kernel | core/ai_kernel.py | ✅ |
| L4 | Proof of History | blockchain/consensus/ | ✅ |
| L5 | ATCNet P2P | modules/atcnet/ | ✅ |
| L6 | Smart Contracts | modules/contracts/ | ✅ |
| L7 | API Gateway | modules/gateway/ | ✅ |
| L8 | Franchise DAO | modules/franchise/ | 📋 |
| L9 | Agent Registry | backend/api/ | ✅ |
| L10 | Dashboard UI | modules/ui/ | ✅ |
| L11 | DeFi | modules/contracts/bridge/ | 📋 |
| L12 | Shivamon NFT | modules/shivamon/ | 📋 |

## 📋 Offene Issues

| # | Titel | Priorität | Kritischer Pfad |
|---|-------|-----------|-----------------|
| 🔴 #8 | Multi-Node Testnet | HIGH | **Blocker für MK3** |
| 🟡 #18 | Docker Compose 5-Node | MEDIUM | Voraussetzung für #8 |
| 🟡 #19 | Node-Monitoring Dashboard | MEDIUM | Nach #18 |
| 🟡 #7 | Build System EXE/AppImage | MEDIUM | — |
| 🟡 #11 | Shivamon Breeding Gen 2 | MEDIUM | Sprint 3.x |
| 🟡 #12 | Solidity Smart Contracts | MEDIUM | Sprint 3.11 |
| 🟡 #13 | ATC Marketplace | MEDIUM | Sprint 3.10 |
| 🟢 #10 | Cross-Chain Bridge ATC↔EVM | LOW | Sprint 3.10 |

## 🔗 Links

- 📋 [Notion Roadmap](https://www.notion.so/373b826db85c8125ba83f04995191bf0)
- 📊 [Google Sheets Dashboard](https://docs.google.com/spreadsheets/d/1xR5c24NrtYC58OsGrLaUHkQUiL_O6eYVyx8KmFcvBD4/edit)
- 📖 [KAI-OS Wiki](docs/wiki/kai-os/)
- 📄 [Whitepaper](docs/whitepaper/WHITEPAPER.md)

## 📜 Migrierte Repositories (archiviert)

Alle folgenden Repos wurden in dieses Monorepo integriert und archiviert:

`atc-kernel` · `atc-gateway` · `atc-contracts` · `atclang` · `atcnet` · `atc-ui` · `atc-shivamon` · `atc-franchise` · `atc-standards` · `atc-whitepaper` · `atc-kernel-wiki` · `atc-gateway-wiki` · `atc-contracts-wiki` · `atclang-wiki` · `atcnet-wiki` · `atc-ui-wiki` · `atc-shivamon-wiki` · `atc-franchise-wiki` · `atc-standards-wiki` · `a-townchain-os-wiki` · `atclang-wiki` · `ShivaCoreDev/kai-os-wiki` · `ShivaCoreDev/franchise-factory-wiki`

---

*Auto-generiert von Superagent | Stand: 2026-06-10 | Apache 2.0*
