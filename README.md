# 🌌 A-TownChain OS — v2.0

> **Autonomous Franchise Factory** | ShivaOS | Blockchain + AI + Gaming

## 🏗 Architektur

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND                            │
│              frontend/index.html                        │
│           (ShivaOS Dashboard — Browser)                 │
└───────────────────────┬─────────────────────────────────┘
                        │  HTTP (Port 3000)
                        │  NUR über api.js
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  API GATEWAY  ⚡                         │
│               gateway/main.py                           │
│          Port 4000 — Vermittler / Proxy                 │
│                                                         │
│  • Authentifizierung (API Key)                          │
│  • Rate Limiting                                        │
│  • Request Logging                                      │
│  • Service Routing                                      │
└──┬──────────┬──────────┬──────────┬────────────┬────────┘
   │          │          │          │            │
   ▼          ▼          ▼          ▼            ▼
┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────┐
│ Core │  │Chain │  │Wallet│  │  AI  │  │  Game    │
│:5000 │  │:5001 │  │:5002 │  │:5003 │  │  :5004   │
└──────┘  └──────┘  └──────┘  └──────┘  └──────────┘
   BACKEND SERVICES (Flask Microservices)
```

## 📁 Struktur

```
a-townchain-os/
├── frontend/          # UI Dashboard (Browser)
│   ├── index.html     # ShivaOS Dashboard
│   └── assets/
│       ├── js/api.js  # Spricht NUR mit Gateway
│       └── css/
│
├── gateway/           # API Gateway (Vermittler)
│   ├── main.py        # Port 4000
│   ├── router.py      # Service Routing
│   └── middleware/    # Auth, RateLimit, Logger
│
├── backend/           # Backend Services
│   ├── main.py        # Core Service :5000
│   └── api/           # Routes
│
├── core/              # Kernel, EventBus, ModuleLoader
├── plugins/           # Wallet, GameEngine, AI
├── blockchain/        # Smart Contracts
├── build/             # Build System
└── config/            # Settings
```

## 🚀 Starten

```bash
# 1. Gateway starten
cd gateway && pip install -r requirements.txt
python main.py        # Port 4000

# 2. Backend starten
cd backend && python main.py   # Port 5000

# 3. Frontend öffnen
open frontend/index.html
```

## 🔗 API Endpoints (alle über Gateway Port 4000)
| Method | Endpoint | Service |
|--------|----------|---------|
| GET | /api/status | Core :5000 |
| GET | /api/blockchain/info | Chain :5001 |
| GET | /api/wallet/balance/:addr | Wallet :5002 |
| POST | /api/wallet/send | Wallet :5002 |
| POST | /api/ai/query | AI :5003 |
| GET | /api/game/shivamon/:id | Game :5004 |

---
*Built with Aurora AI Agent — ShivaOS v2.0*
