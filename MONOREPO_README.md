# A-TownChain OS — Monorepo v3.0.0

> **Alle 22 Repositories zusammengeführt in einem einzigen Monorepo.**
> Stand: 2026-06-10 | Migriert von: A-TownChain-Okosystems/* + ShivaCoreDev/kai-os-wiki

---

## 📦 Struktur

```
a-townchain-os/
├── modules/              ← Ausführbarer Quellcode (aus separaten Repos)
│   ├── kernel/           ← atc-kernel — L2 ShivaOS Microkernel
│   ├── gateway/          ← atc-gateway — L7 API Gateway :4000
│   ├── contracts/        ← atc-contracts — Smart Contracts (ATC-8300, Governance, Shivamon)
│   ├── atclang/          ← atclang — ATCLang Compiler, VM, REPL
│   ├── atcnet/           ← atcnet — P2P Netzwerk, Kademlia DHT
│   ├── ui/               ← atc-ui — Neon Dashboard Frontend
│   ├── shivamon/         ← atc-shivamon — L12 NFT Gaming Engine
│   ├── franchise/        ← atc-franchise — L10/L8 Business DAO
│   └── standards/        ← atc-standards — ATC/ATS Protokoll-Standards
│
├── docs/
│   ├── whitepaper/       ← atc-whitepaper — Offizielles Whitepaper v2.1.0
│   └── wiki/
│       ├── kai-os/       ← ShivaCoreDev/kai-os-wiki — KAI-OS Theorie & Architektur
│       ├── kernel/       ← atc-kernel-wiki
│       ├── gateway/      ← atc-gateway-wiki
│       ├── contracts/    ← atc-contracts-wiki
│       ├── atclang/      ← atclang-wiki
│       ├── atcnet/       ← atcnet-wiki
│       ├── ui/           ← atc-ui-wiki
│       ├── shivamon/     ← atc-shivamon-wiki
│       ├── franchise/    ← atc-franchise-wiki
│       ├── standards/    ← atc-standards-wiki
│       └── overview/     ← a-townchain-os-wiki
│
├── backend/              ← API-Server, Orchestrator, DB
├── blockchain/           ← Chain, Consensus, Wallet
├── core/                 ← Kernel-Core
├── frontend/             ← Dashboard HTML/JS/CSS
├── atclang/              ← ATCLang (bestehend)
└── shivaos/              ← ShivaOS Kernel-Komponenten
```

## 🚀 Schnellstart

```bash
# Alle Abhängigkeiten installieren
pip install -r requirements.txt

# Gateway starten (Port 4000)
python modules/gateway/main.py

# ATCLang REPL
python modules/atclang/repl/repl.py

# Testnet (Docker) — Issue #18
docker-compose up  # coming soon
```

## 📋 Offene Issues
Siehe [GitHub Issues](https://github.com/A-TownChain-Okosystems/a-townchain-os/issues)

| # | Titel | Priorität |
|---|-------|-----------|
| #8 | Multi-Node Testnet | 🔴 HIGH |
| #18 | Docker Compose 5-Node | 🟡 MEDIUM |
| #19 | Node-Monitoring Dashboard | 🟡 MEDIUM |
| #7 | Build System EXE/AppImage | 🟡 MEDIUM |

## 🔗 Migrierte Repositories

| Ehemaliges Repo | Jetzt unter | Status |
|----------------|-------------|--------|
| atc-kernel | modules/kernel/ | ✅ |
| atc-gateway | modules/gateway/ | ✅ |
| atc-contracts | modules/contracts/ | ✅ |
| atclang | modules/atclang/ | ✅ |
| atcnet | modules/atcnet/ | ✅ |
| atc-ui | modules/ui/ | ✅ |
| atc-shivamon | modules/shivamon/ | ✅ |
| atc-franchise | modules/franchise/ | ✅ |
| atc-standards | modules/standards/ | ✅ |
| atc-whitepaper | docs/whitepaper/ | ✅ |
| kai-os-wiki | docs/wiki/kai-os/ | ✅ |
| atc-*-wiki (10x) | docs/wiki/*/ | ✅ |

*Auto-generiert von Superagent — 2026-06-10*
