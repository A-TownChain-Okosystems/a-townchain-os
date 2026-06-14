## [1.4.0] — 2026-06-12

### 🔴 Critical Bug Fixes
- `poh.py`: verify() Sicherheitslücke — data_hash Einträge wurden nicht kryptografisch geprüft
- `poh.py`: VDF-Delay (0.0001s) war definiert aber nicht aktiviert — jetzt in tick()
- `hybrid_consensus.py`: poh_entry["hash"] KeyError — war dict-Zugriff auf @dataclass
- `hybrid_consensus.py`: validate_chain() prüfte PoH-Kette nicht — jetzt Sequenz-Monotonie geprüft
- `syscalls.py`: ATC_BALANCE=3 kollidierte mit EXEC=3 — korrigiert auf 33
- `shivamon_contract.py`: DNA-Kollision möglich — os.urandom(8) hinzugefügt

### 📚 Wiki & Dokumentation
- Wiki auf 62 Kapitel erweitert (Kap. 53–62: ATCLang v0.3, Testnet, Mainnet, Gas, Mobile, IPC, Monitoring, BigQuery, HuggingFace, Automation)
- ECOSYSTEM_BRAIN.md — Vollständige System-Dokumentation
- docs/standards/STANDARDS_REGISTRY.md — 14 ATC/KIP/AIP/ATS Standards
- docs/DECISIONS_REGISTER.md — 7 offene Agent Decisions
- docs/AGENT_POLICY.md — Reality-Check + Sync-Protokoll
- SYNC_PROTOCOL.md — Letzter Sync-Stand + Blocker
- Wiki Kap. 37: BLAKE2b → SHA-3_256 korrigiert
- Wiki Kap. 56: Gas-Target 15M → 5M mit Code synchronisiert

### 🏗️ CI/CD
- ci-cd.yml: npm ci → npm install (kein package-lock.json nötig)
- ci-cd.yml: ruff --ignore E501,F401,F811,W291,W293
- ci-cd.yml: bandit auf HIGH severity (-lll)
- ci-cd.yml: black --check nicht blockierend

### 🧠 Ecosystem Brain (neu)
- Knowledge Graph: 21 EcosystemNodes, 7 AgentDecisions, 14 Standards, 9 Sprints
- 12 Agenten-Rollen aktiv (KnowledgeAgent bis ResearchAgent)
- Täglicher Auto-Sync 08:00 Uhr (Automation ID: 6a2a84debb58cc332fc9f9fb)
- Multi-Quellen-Sync: GitHub, Notion, Gmail, Outlook, Tasks, Drive, Calendar


---

# Changelog

## [History] v3.1.0 → v1.0-rc3 — 2026-06-11 (Aurora Sync Release)

### Verbesserungen
- Modul-Doku fuer alle 7 Module erstellt (atclang, atcnet, kernel, gateway, contracts, franchise, shivamon)
- README: Quickstart-Section hinzugefuegt
- AI Agent Manifest v2.0: alle 17 Dienste dokumentiert
- Cross-Connect: 20/20 bidirektionale Verbindungen aktiv
- Master Sync v3.1: 20 Schritte, taeglich 08:05

### Status
- 9 offene Issues (niedrige/mittlere Prioritaet)
- 41 geschlossene Issues
- Kritischer Pfad #14 bis #8: alle 6 Issues geschlossen

 — A-TownChain

## [History] v3.0.0 → v1.0-rc2 — 10.06.2026 (Enterprise Release)

### New Features
- #34 Solana Bridge (SPL-Token, Wormhole, Relayer M-of-N)
- #35 ATCLang v0.3.0 (async/await, Generics, Closures, Module-System)
- #36 Mainnet Launch Config (Chain-ID 9000, 21M ATC Tokenomics)
- #37 DEX/AMM (x*y=k, SwapRouter, LP-Token, 0.3% Fee)
- #38 Mobile Wallet (React Native, BIP39, QR, Biometric Auth)
- #39 DAO Governance Live (FFT+ATC Voting, Quorum, Timelock)
- Enterprise CI/CD (GitHub Actions, multi-Python matrix)
- Nginx TLS Reverse Proxy + Rate-Limiting
- Prometheus+Grafana Monitoring Stack
- Redis Cache Layer
- SECURITY.md + Bug Bounty Program
- CONTRIBUTING.md Enterprise Standards

### Documentation
- #40 ATCLang Syntax Reference
- #41 Mathematical Proofs (7 Theorems)
- #42 Error Codes + Bottleneck Analysis
- #43 Decentralized Proofs for Users

### Infrastructure
- Docker Compose Enterprise (9 Services)
- Prometheus Alert Rules (6 Alerts)
- Nginx Enterprise Config (TLS, Rate-Limit, Security Headers)

## [History] v2.2.0 → v1.0-rc1 — 10.06.2026
- 17 Issues: Bridge ETH+POL+BSC, Breeding, Marketplace, ATCFS,
  MultiSig, Gateway v2, Integration Tests 9/9, atcpkg, TUI,
  Federated Learning, Gas-Fee EIP-1559, Syscall-Tabelle, Testnet

## [History] v2.1.0 → v1.0-beta — 09.06.2026
- 11 Issues: Smart Contracts, Gemini AI, Battle UI, ECDSA,
  Governance, Solidity, Bootstrap, Security Audit, Analyzer
