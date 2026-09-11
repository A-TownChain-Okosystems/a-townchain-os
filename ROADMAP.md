---
document_id: ATC-DOC-RDM-001
title: Repository Roadmap
version: 1.0.0
status: active
owner: A-TownChain-Okosystems
created: 2026-09-07
updated: 2026-09-11
standard: ATC-STD-MD-001
---

# Roadmap — a-townchain-os

## Meilensteine (Lauffähigkeits-Roadmap M1–M8, AD-027)

- **M1:** Sprachanpassungen & ATCLang (G1 ✅ → G2 offen, AD-019 Phase 1 abgeschlossen)
- **M2:** Kernel Boot & Core Integration (atc-shivacore 674/674 Tests ✅)
- **M3:** KI-Layer Integration (aurora-ai / AAS-001..025)
- **M4:** Blockchain Infrastructure (2 Nodes, Chain-ID 658467, Smart Contract Execution auf ATVM)
- **M5:** OS-Schicht & Kernel-Services
- **M6:** 13 Blockchain Services Integration
- **M7:** Genesis Engine & Chronicles Integration (Spiele/NFT auf Chain)
- **M8:** Full Monorepo Release Candidate & Audit Finalisierung

## KAI-OS Core Runtime Track (S01–S26, Owner-Direktive 11.09.2026)

Implementierungsreihenfolge nach Systemkritikalität — Spezifikation: [docs/architecture/KAI-CORE-RUNTIME-001.md](docs/architecture/KAI-CORE-RUNTIME-001.md)

- **S01–S03:** Node Daemon + Supervisor + Lifecycle
- **S04–S06:** Resource Manager + Sandbox
- **S07–S09:** P2P Transport + Discovery + Peer Security
- **S10–S12:** State Sync + Snapshots + Verification
- **S13–S15:** AI Agent Runtime + IPC
- **S16–S18:** Keyring + Capability Security
- **S19–S20:** Immutable Audit / Event System
- **S21–S22:** Model Registry + Verified Cache
- **S23–S24:** kai-os CLI + Control API
- **S25:** ATC Module/Package Manager
- **S26:** Production Readiness Gate **GATE-KAI-001** (12 Test-Kategorien)

> Grundsatz: **Policy → Sandbox → Capability → Execution** · KI erkennt → Policy entscheidet → System führt aus.
