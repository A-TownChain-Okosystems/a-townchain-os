# A-TownChain Monorepo Structure

> K2 Konsolidierung — Verzeichnisstruktur für Release v1.0

## Übersicht

```
a-townchain-os/
├── src/                    # Python Backend (K3)
│   ├── core/               # ShivaCore Kernel
│   ├── network/            # ATCNet P2P
│   ├── gateway/            # API Gateway
│   ├── contracts/           # Smart Contracts
│   ├── game/               # ShivaMon
│   ├── franchise/          # Franchise Factory
│   ├── atclang/            # ATCLang Compiler
│   ├── blockchain/         # Blockchain Core
│   └── modules/            # Shared Modules
├── frontend/               # TypeScript Frontend (K4)
│   └── src/
├── docker/                 # Docker Setup (K5)
│   └── docker-compose.yml
├── scripts/                # Build/Start/Stop (K5)
│   ├── build.sh
│   ├── start.sh
│   └── stop.sh
├── tests/                  # Test Suite (K7)
│   ├── unit/
│   │   ├── core/
│   │   ├── blockchain/
│   │   ├── network/
│   │   ├── contracts/
│   │   └── atclang/
│   ├── integration/
│   └── e2e/
├── .github/workflows/      # CI/CD (K6)
│   └── build.yml
├── docs/                   # Documentation
└── config/                 # Configuration
```

## Migration Status

| Sprint | Task | Status |
|--------|------|--------|
| K2.1 | Verzeichnisstruktur | ✅ Done |
| K2.2 | src/ Python-Module | ✅ Done |
| K2.3 | frontend/ TypeScript | ✅ Structure |
| K2.4 | docs/ Wiki-Content | Pending |
| K2.5 | docker/ Multi-Service | ✅ docker-compose.yml |
| K2.6 | scripts/ Build/Start/Stop | ✅ Done |
| K2.7 | tests/ Structure | ✅ Done |
| K2.8 | CI/CD Templates | ✅ build.yml |

## Legacy Directories (to be migrated in K3)

The following directories contain legacy code that will be migrated into `src/` during K3:
- `core/` → `src/core/`
- `blockchain/` → `src/blockchain/`
- `modules/` → `src/modules/`
- `atclang/` → `src/atclang/`
- `gateway/` → `src/gateway/`
- `backend/` → `src/` (merged)
- `shivaos/` → `src/core/`
- `shivacore/` → `src/core/`

*Created by Agent Aurora — K2 Konsolidierung*
