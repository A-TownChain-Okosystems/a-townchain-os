# 🌌 A-TownChain OS — v2.0

> **Autonomous Franchise Factory** | ShivaOS | Blockchain + AI + Gaming

## 🏗 Architecture

```
a-townchain-os/
├── frontend/          # UI Dashboard (HTML/CSS/JS)
│   ├── index.html     # ShivaOS Dashboard
│   └── assets/        # JS API Client, CSS Variables
│
├── backend/           # Python REST API (Flask)
│   ├── main.py        # Entry point
│   ├── api/           # Routes: /status /blockchain /wallet /ai
│   └── requirements.txt
│
├── core/              # Kernel, EventBus, ModuleLoader
├── plugins/           # Wallet, GameEngine, AI Module
├── blockchain/        # Smart Contracts, Nodes
├── build/             # Build System & EXE Installer
└── config/            # Settings & Environment
```

## 🚀 Quick Start

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
# Open frontend/index.html in browser
# or serve:
python -m http.server 3000
```

## 🔗 API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/status | System status |
| GET | /api/blockchain/info | Chain info |
| GET | /api/wallet/balance/:address | ATC balance |
| POST | /api/transfer | Send ATC |
| POST | /api/ai/query | AI query |

---
*Built with Aurora AI Agent — ShivaOS v2.0*
