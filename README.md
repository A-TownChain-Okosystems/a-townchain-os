# 🌌 A-TownChain OS — v2.0

<div align="center">

![A-TownChain OS](https://img.shields.io/badge/version-2.0-a259ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-00d1ff?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-00ffb3?style=for-the-badge&logo=flask)
![License](https://img.shields.io/badge/license-MIT-ff2d78?style=for-the-badge)

**Autonomous Franchise Factory — ShivaOS v2.0**

*Blockchain × AI × Gaming × Operating System Ecosystem*

</div>

---

## 📖 Inhaltsverzeichnis

1. [Überblick](#-überblick)
2. [Architektur](#-architektur)
3. [Projektstruktur](#-projektstruktur)
4. [Installation](#-installation)
5. [API Dokumentation](#-api-dokumentation)
6. [Smart Contracts](#-smart-contracts)
7. [ATC Token Standards](#-atc-token-standards)
8. [Frontend Dashboard](#-frontend-dashboard)
9. [Entwicklung](#-entwicklung)
10. [Roadmap](#-roadmap)

---

## 🌍 Überblick

A-TownChain OS ist ein vollständiges, modulares Technologie-Ökosystem bestehend aus:

| Komponente | Beschreibung | Status |
|-----------|-------------|--------|
| 🏠 **ShivaOS** | Futuristisches Dashboard (Browser-basiert) | ✅ v2.0 |
| ⛓ **A-TownChain** | Eigene Blockchain mit PoI+PoS Konsens | 🔨 Phase 1 |
| 🧠 **AI Orchestrator** | Gemini 2.0 + lokale Modelle | 🔨 Phase 2 |
| 🎮 **Shivamon** | NFT-basiertes Battle Game (ATC-9000) | 📋 Phase 3 |
| 🏭 **Franchise Factory** | Autonomes Deployment-System | 📋 Phase 3 |
| 💰 **ATC Wallet** | Multi-Standard Token Wallet | 🔨 Phase 2 |

---

## 🏗 Architektur

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│                  frontend/index.html                         │
│            ShivaOS Dashboard  (Browser :3000)                │
│                  ↓  api.js ↑                                 │
│         Spricht NUR mit dem API Gateway                      │
└─────────────────────┬────────────────────────────────────────┘
                      │ HTTP/JSON
                      ▼
┌──────────────────────────────────────────────────────────────┐
│                    API GATEWAY  ⚡                            │
│                  gateway/main.py                             │
│                     Port 4000                                │
│                                                              │
│   🔑 Authentifizierung    🚦 Rate Limiting                   │
│   📋 Request Logging      🔀 Service Routing                 │
└──┬───────────┬───────────┬──────────┬──────────┬────────────┘
   │           │           │          │          │
   ▼           ▼           ▼          ▼          ▼
┌──────┐  ┌────────┐  ┌────────┐  ┌──────┐  ┌──────┐
│ Core │  │ Chain  │  │ Wallet │  │  AI  │  │ Game │
│:5000 │  │ :5001  │  │ :5002  │  │:5003 │  │:5004 │
└──┬───┘  └───┬────┘  └───┬────┘  └──┬───┘  └──┬───┘
   │          │           │           │          │
   └──────────┴───────────┴───────────┴──────────┘
                      CORE LAYER
              ┌───────────────────────┐
              │  core/kernel.py       │
              │  core/event_bus.py    │
              │  core/module_loader.py│
              └───────────┬───────────┘
                          │
              ┌───────────▼───────────┐
              │  BLOCKCHAIN LAYER     │
              │  blockchain/contracts/│
              │  ATC Token Standards  │
              └───────────────────────┘
```

---

## 📁 Projektstruktur

```
a-townchain-os/
│
├── 🖥  frontend/                  # Browser UI
│   ├── index.html                # ShivaOS Dashboard
│   └── assets/
│       ├── js/api.js             # API Client (→ Gateway only)
│       └── css/variables.css     # Design System
│
├── ⚡  gateway/                   # API Gateway (Vermittler)
│   ├── main.py                   # Entry Point :4000
│   ├── router.py                 # Service Routing
│   ├── requirements.txt
│   └── middleware/
│       ├── auth.py               # API Key Auth
│       ├── rate_limit.py         # Rate Limiter
│       └── logger.py             # Request Logger
│
├── ⚙️  backend/                   # Backend Services
│   ├── main.py                   # Core Service :5000
│   ├── requirements.txt
│   └── api/
│       ├── server.py             # Flask App Factory
│       └── routes/
│           ├── blockchain.py     # Chain Routes :5001
│           └── wallet.py         # Wallet Routes :5002
│
├── 🧠  core/                      # OS Kernel
│   ├── kernel.py                 # System Kernel
│   ├── event_bus.py              # Event-Driven Bus
│   └── module_loader.py          # Dynamic Plugin Loader
│
├── 🔌  plugins/                   # Erweiterungsmodule
│   └── wallet.py                 # ATC Wallet Plugin
│
├── ⛓  blockchain/                 # Blockchain Layer
│   └── smart_contracts.py        # ATC Contract (Python)
│   └── contracts/                # Solidity Contracts (Phase 2)
│
├── 📦  build/                     # Build & Export
│   └── build.py                  # PyInstaller Build Script
│
└── ⚙️  config/                    # Konfiguration
    └── settings.json             # System Settings
```

---

## 🚀 Installation

### Voraussetzungen
- Python 3.10+
- pip
- Git

### 1. Repository klonen
```bash
git clone https://github.com/ShivaCoreDev/a-townchain-os.git
cd a-townchain-os
```

### 2. Gateway starten
```bash
cd gateway
pip install -r requirements.txt
cp .env.example .env
python main.py
# → läuft auf http://localhost:4000
```

### 3. Backend starten
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
# → läuft auf http://localhost:5000
```

### 4. Frontend öffnen
```bash
# Option A: direkt im Browser
open frontend/index.html

# Option B: lokaler Server
python -m http.server 3000 --directory frontend
# → http://localhost:3000
```

---

## 🔗 API Dokumentation

Alle API-Calls laufen über das **Gateway auf Port 4000**.

### Gateway Health
```
GET http://localhost:4000/gateway/health
```
```json
{
  "gateway": "online",
  "version": "2.0",
  "services": {
    "status": "online",
    "blockchain": "online",
    "wallet": "online"
  }
}
```

### Endpoints

| Method | Endpoint | Service | Beschreibung |
|--------|----------|---------|-------------|
| `GET` | `/api/status` | Core :5000 | System Status |
| `GET` | `/api/modules` | Core :5000 | Geladene Module |
| `GET` | `/api/blockchain/info` | Chain :5001 | Chain Informationen |
| `GET` | `/api/blockchain/blocks` | Chain :5001 | Block Liste |
| `GET` | `/api/blockchain/tx/:id` | Chain :5001 | Transaction |
| `GET` | `/api/wallet/balance/:addr` | Wallet :5002 | ATC Balance |
| `POST` | `/api/wallet/send` | Wallet :5002 | Transfer senden |
| `POST` | `/api/ai/query` | AI :5003 | AI Anfrage |
| `GET` | `/api/game/shivamon/:id` | Game :5004 | Shivamon Info |

### Authentifizierung
```http
X-API-Key: atc-dev-key-2025
```

---

## ⛓ Smart Contracts

> 📋 Aktuelle Planung: [Issue #1](https://github.com/ShivaCoreDev/a-townchain-os/issues/1)

### ATC Token (ATC-8300)
```python
# blockchain/smart_contracts.py
class ATCToken:
    total_supply = 1_000_000
    
    def transfer(self, sender, receiver, amount): ...
    def approve(self, owner, spender, amount): ...
    def allowance(self, owner, spender): ...
```

### Geplante Contracts
| Contract | Standard | Beschreibung |
|---------|---------|-------------|
| `ATCToken.sol` | ATC-8300 | Fungible Token (ERC20) |
| `Shivamon.sol` | ATC-9000 | NFT Battle Creature |
| `ATCGovernance.sol` | ATC-9900 | DAO Voting |
| `GenesisToken.sol` | ATC-001 | Genesis Block Token |

---

## 🪙 ATC Token Standards

| Standard | Typ | Beschreibung |
|---------|-----|-------------|
| ATC-001 | Genesis | Ursprungs-Token |
| ATC-8300 | Fungible | Haupt-Token (wie ERC20) |
| ATC-9000 | NFT | Shivamon Creature Token |
| ATC-9900 | Governance | Voting & DAO |

---

## 🖥 Frontend Dashboard

Das ShivaOS Dashboard ist ein vollständiges Browser-OS mit:

- **14-Item Sidebar** — Navigation zwischen allen Modulen
- **AI Orchestrator Panel** — Live AI Status
- **Network Node Visualizer** — Chain-Verbindungen
- **Code Center** — Integrierter Editor mit Datei-Explorer
- **Dock** — 10 App-Icons für Schnellzugriff
- **Neon Design System** — Futuristisches Dark Theme

### Design Tokens
```css
--purple:  #a259ff   /* Primärfarbe */
--cyan:    #00d1ff   /* Akzent */
--green:   #00ffb3   /* Status Online */
--pink:    #ff2d78   /* Alert / Error */
--bg:      #05080f   /* Hintergrund */
```

---

## 🛠 Entwicklung

### Branch-Strategie
```
main
├── feature/core        # Kernel & Event Bus
├── feature/blockchain  # Smart Contracts
├── feature/ui          # Dashboard
└── feature/build       # Build System
```

### Codex Regeln (verbindlich)
1. **Keine Inline-Logik** — alles in Module
2. **Plugin-System Pflicht** — alles erweiterbar
3. **Build getrennt** — Build-Code ≠ App-Code
4. **Core kennt keine Plugins**
5. **Kein Agent ohne Review auf main**

---

## 📍 Roadmap

- [x] ShivaOS Dashboard v2.0
- [x] API Gateway (Vermittler)
- [x] Frontend/Backend Trennung
- [x] Core Kernel + EventBus
- [ ] Smart Contracts (ATC-8300) — [Issue #1](https://github.com/ShivaCoreDev/a-townchain-os/issues/1)
- [ ] Gemini AI Integration
- [ ] Shivamon Game Engine
- [ ] ATC Wallet (vollständig)
- [ ] Franchise Factory Automation
- [ ] EXE Installer Build
- [ ] Dezentrale Nodes

---

<div align="center">

Built with 💜 by **ShivaCoreDev** × **Aurora AI Agent**

*ShivaOS v2.0 — A-TownChain Ecosystem*

</div>
