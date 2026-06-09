# A-TownChain OS — KAI-OS v2.0.0

> **Das einzige Haupt-Repository des A-TownChain Ökosystems.**
> KI-Blockchain-Betriebssystem · 13-Layer NFT-Architektur · 26 Sprints · 4 Phasen

[![Version](https://img.shields.io/badge/Version-v2.0.0-blue)](https://github.com/A-TownChain-Okosystems/a-townchain-os/blob/main/CHANGELOG.md)
[![KAI-OS](https://img.shields.io/badge/KAI--OS-31%20Kapitel-purple)](https://github.com/A-TownChain-Okosystems/a-townchain-os/blob/main/docs/kai-os-wiki.md)
[![Tests](https://img.shields.io/badge/Tests-19%2F19%20grün-brightgreen)](https://github.com/A-TownChain-Okosystems/a-townchain-os/blob/main/tests/)
[![Layer](https://img.shields.io/badge/Layer-L0--L12-orange)](https://github.com/A-TownChain-Okosystems/a-townchain-os/blob/main/ECOSYSTEM.md)
[![ATX](https://img.shields.io/badge/ATX--Standards-186%20Module-green)](https://github.com/A-TownChain-Okosystems/a-townchain-os/blob/main/docs/standards/ATC_STANDARDS.md)

---

## 📂 Repository-Struktur

```
a-townchain-os/
├── blockchain/          # L4: Consensus (PoH→PoS→PoW), Contracts, Wallet, DID
│   ├── consensus/       #   poh.py · hybrid_consensus.py · pow.py · pos.py
│   ├── contracts/       #   ATC-8300, ATC-9000, ATC-9900, Bridge, Solidity
│   ├── nodes/           #   bootstrap.py · discovery.py · p2p_propagation.py
│   └── wallet/          #   keygen.py · ecdsa.py · did.py
├── backend/             # L9: REST API, Orchestrator, DB
│   ├── api/             #   server.py · routes/ · orchestrator/
│   └── db/              #   schema.sql · repository.py
├── gateway/             # L7: API Gateway :4000 (Auth, Rate-Limit, Circuit-Breaker)
├── core/                # L3: KI-Kernel, EventBus, ModuleLoader, CLI
├── atclang/             # L2–L4: Proprietäre Sprache (Lexer, Parser, VM, REPL)
├── shivaos/             # L2: Microkernel, IPC, ATCFS, P2P
├── franchise_factory/   # L10/L8: Business DAO, Vault, Revenue-Share
├── frontend/            # L10: Neon Dashboard (Wallet, Explorer, AI)
├── tests/               # 19 Tests (alle grün ✅)
├── docs/                # Vollständige Dokumentation
│   ├── kai-os-wiki.md   #   31 Kapitel · vollständige OS-Spezifikation
│   ├── architecture/    #   Kernel, Gateway, Consensus, P2P, ATCFS
│   ├── ai/              #   Gemini, LLM-Router, AI Safety
│   ├── standards/       #   ATC-0001–0009, ATS-1000–1007
│   ├── issues/          #   14+ Issue-Dokumentationen
│   └── roadmap/         #   26 Sprints, 4 Phasen
├── docker-compose.yml   # 6 Services: bootstrap, backend, gateway, frontend, postgres, prometheus
├── ECOSYSTEM.md         # Alle 23 Repos verlinkt
└── CHANGELOG.md         # Versionshistorie v1.3.1 → v2.0.0
```

---

## 🚀 Schnellstart

```bash
# Klonen
git clone https://github.com/A-TownChain-Okosystems/a-townchain-os.git
cd a-townchain-os

# Mit Docker starten
cp .env.example .env
docker-compose up -d

# Ohne Docker
pip install -r requirements.txt
python3 backend/main.py        # Backend :5000
python3 gateway/main.py        # Gateway :4000
python3 -m blockchain.nodes.bootstrap  # Bootstrap Node :4001

# Tests
python3 tests/test_poh.py      # 8 Tests ✅
python3 tests/test_did.py      # 7 Tests ✅
python3 tests/test_orchestrator.py  # 4 Tests ✅
```

| Service | URL | Beschreibung |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Neon Dashboard |
| Gateway | http://localhost:4000 | API Proxy |
| Backend | http://localhost:5000 | REST API |
| Bootstrap | udp://localhost:4001 | P2P Discovery |
| Prometheus | http://localhost:9090 | Monitoring |

---

## 🏗️ Architektur — 13-Layer NFT

| Layer | Modul | Beschreibung |
|-------|-------|-------------|
| L0 | `docs/standards/` | Security S1–S6 (Querschnitt) |
| L1 | ATPHY Standards | Hardware-Abstraktion |
| L2 | `shivaos/kernel/` | Microkernel, IPC, ATCFS |
| L3 | `core/ai_kernel.py` | KI-Registry, Gemini, LLM-Router |
| L4 | `blockchain/consensus/` | PoH → PoS → PoW (ShivaConsensus™) |
| L5 | `shivaos/net/` | P2P, Kademlia DHT, Bootstrap |
| L6 | `shivaos/fs/` | ATCFS Dateisystem |
| L7 | `gateway/` | API Gateway :4000 |
| L8 | `blockchain/contracts/governance/` | DAO ATC-9900 |
| L9 | `backend/api/orchestrator/` | KI-Agenten, Orchestrator |
| L10 | `frontend/` + `franchise_factory/` | dApps, Business DAO |
| L11 | `blockchain/contracts/` | DeFi: Token, Bridge, Marketplace |
| L12 | `blockchain/contracts/shivamon/` | NFT Gaming |

---

## 🔗 Ökosystem-Repos

| Repo | Layer | Beschreibung |
|------|-------|-------------|
| [shivaos-kernel](https://github.com/A-TownChain-Okosystems/shivaos-kernel) | L2 | Microkernel (eigenständig) |
| [atcnet](https://github.com/A-TownChain-Okosystems/atcnet) | L5 | P2P Stack (eigenständig) |
| [atc-gateway](https://github.com/A-TownChain-Okosystems/atc-gateway) | L7 | Gateway (eigenständig) |
| [atclang](https://github.com/A-TownChain-Okosystems/atclang) | L2–L4 | Sprache (eigenständig) |
| [atc-contracts](https://github.com/A-TownChain-Okosystems/atc-contracts) | L4/L11 | Contracts (eigenständig) |
| [shivamon](https://github.com/A-TownChain-Okosystems/shivamon) | L12 | Gaming (eigenständig) |
| [franchise-factory](https://github.com/A-TownChain-Okosystems/franchise-factory) | L10/L8 | Business DAO (eigenständig) |
| [atc-ui](https://github.com/A-TownChain-Okosystems/atc-ui) | L10 | Dashboard (eigenständig) |
| [atc-standards](https://github.com/A-TownChain-Okosystems/atc-standards) | L0 | Standards |

📋 **[→ Vollständiger Ökosystem-Index (23 Repos)](./ECOSYSTEM.md)**

---

## 📊 Projekt-Status

| Metrik | Wert |
|--------|------|
| Version | v2.0.0 |
| Tests | 19/19 ✅ |
| KAI-OS Wiki | 31 Kapitel |
| ATX-Module | 186 |
| Kritische Blocker gelöst | 4 (ATC-1000, ATN-1000, ATS-1000, ATAUTH-1000) |
| Aktueller Sprint | 2.1–2.2 |
| MK1-Gate ETA | ~4 Tage |

---

*[A-TownChain-Okosystems](https://github.com/A-TownChain-Okosystems) · [@ShivaCoreDev](https://github.com/ShivaCoreDev) · Stand: 2026-06-09*
