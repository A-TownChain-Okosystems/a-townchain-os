# AGENT_MANIFEST.md
> Letzte Aktualisierung: 2026-09-06 21:45 UTC | Aurora Master Sync v3.0 | 22-Repo-Stand (AD-016–AD-024)

## Repositories (22 aktive — AD-016 + AD-024)
### Kern-Plattform (8, AD-016)
| Repo | Rolle | Zustand (AD-020) |
|------|-------|------------------|
| [a-townchain-os-docs](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs) | **WIKI-VAULT** — alles Wissen inkl. `docs/archive/monorepo-full/` | ✅ gefüllt |
| [atclang](https://github.com/A-TownChain-Okosystems/atclang) | ATCLang 1.0 (Rust-first, AD-021/022) | ✅ Rebuild Phase 1 COMPLETE |
| [a-townchain-os](https://github.com/A-TownChain-Okosystems/a-townchain-os) | Monorepo — NUR Integration (AD-017: `scripts/sync_modules.py`) | 🔴 geleert |
| [atc-shivacore](https://github.com/A-TownChain-Okosystems/atc-shivacore) | Microkernel — Rebuild per AD-013 (SC-001…SC-013) | 🔴 geleert |
| [a-townchain](https://github.com/A-TownChain-Okosystems/a-townchain) | Blockchain-Produkt (Chain-ID 658467) | 🔴 geleert |
| [globus-os](https://github.com/A-TownChain-Okosystems/globus-os) | OS-Produkt (Userspace) | 🔴 geleert |
| [aurora-ai](https://github.com/A-TownChain-Okosystems/aurora-ai) | AI-Produkt | 🔴 geleert |
| [genesis-engine](https://github.com/A-TownChain-Okosystems/genesis-engine) | Game-Engine-Produkt | 🔴 geleert |

### Vertikale Repos (14, AD-024 — 06.09.2026 erstellt)
| Repo | Priorität | Inhalt |
|------|-----------|--------|
| [atc-sdk](https://github.com/A-TownChain-Okosystems/atc-sdk) | P0 | Developer Platform (rust/ts/python/cli) — Vault-Restore |
| [atc-node](https://github.com/A-TownChain-Okosystems/atc-node) | P0 | Executable Node (Networking/RPC/Storage/Consensus) |
| [atc-contracts](https://github.com/A-TownChain-Okosystems/atc-contracts) | P0 | Smart-Contract-Standards — Vault-Restore |
| [atc-wallet](https://github.com/A-TownChain-Okosystems/atc-wallet) | P0 | Wallet, eigene Security Boundary — Vault-Restore |
| [atc-explorer](https://github.com/A-TownChain-Okosystems/atc-explorer) | P1 | Block Explorer — Vault-Restore |
| [atc-indexer](https://github.com/A-TownChain-Okosystems/atc-indexer) | P1 | Indexing Pipeline |
| [atc-mining](https://github.com/A-TownChain-Okosystems/atc-mining) | P1 | Mining-Stack (PoW-Regeln bleiben im Core) |
| [atc-interop](https://github.com/A-TownChain-Okosystems/atc-interop) | P1 | Bridges/IBC — eigene Sicherheitsdomäne |
| [genesis-chronicles](https://github.com/A-TownChain-Okosystems/genesis-chronicles) | P1 | NFT-Game „Genesis Chronicles" (ex-shivamon, AD-025) — Vault-Restore |
| [atc-oracle](https://github.com/A-TownChain-Okosystems/atc-oracle) | P2 | External Data Binding |
| [atc-storage](https://github.com/A-TownChain-Okosystems/atc-storage) | P2 | Dezentrale Storage-Schicht |
| [atc-launchpad](https://github.com/A-TownChain-Okosystems/atc-launchpad) | P2 | Token/NFT-Launchpad |
| [atc-marketplace](https://github.com/A-TownChain-Okosystems/atc-marketplace) | P2 | NFT/Asset-Marktplatz |
| [atc-compute](https://github.com/A-TownChain-Okosystems/atc-compute) | P2 | Dezentrale Compute-Schicht |

> **Rebuild-Reihenfolge (AD-020):** atc-shivacore SC-001+ → übrige Produkt-Repos (Launch-Stack bei Bedarf aus Vault).
> **Chain-ID:** 658467 (AD-004 RESOLVED). **Mainnet-Launch: per AD-023 AUFGEHOBEN — kein Datum.**

## Integrationen (17 aktiv)
| Integration | Status | Zweck |
|-------------|--------|-------|
| GitHub | ✅ | Code + Docs Hosting |
| Notion | ✅ | Roadmap + Protokolle |
| Google Sheets | ✅ | Dashboard + Metriken |
| Google Docs | ✅ | Projekt-Reports |
| Google Slides | ✅ | Sprint-Präsentationen |
| Google Calendar | ✅ | Sprint-Deadlines |
| Google Drive | ✅ | Datei-Archiv |
| Google Analytics | ✅ | Web-Traffic |
| Google BigQuery | ✅ | Langzeit-Metriken |
| Google Search Console | ✅ | SEO + Keywords |
| Google Tasks | ✅ | Issue-Tracking |
| Google Meet | ✅ | Standup-Meetings |
| Google Classroom | ✅ | Entwickler-Kurse |
| Gmail | ✅ | Status-Reports |
| Microsoft Outlook | ✅ | Status-Reports |
| Microsoft Teams | ✅ | Team-Kommunikation |
| Microsoft OneDrive | ✅ | Cross-Cloud-Backup |
| Hugging Face | ✅ | KI-Modelle |

## Google Sheets Dashboard
ID: 1xR5c24NrtYC58OsGrLaUHkQUiL_O6eYVyx8KmFcvBD4
URL: https://docs.google.com/spreadsheets/d/1xR5c24NrtYC58OsGrLaUHkQUiL_O6eYVyx8KmFcvBD4

## Notion
- Roadmap: 373b826d-b85c-8125-ba83-f04995191bf0
- Tagesprotokoll: 37bb826d-b85c-81c4-bdd4-cfc0dc74de7e
- Live-Status: 379b826d-b85c-81f4-9b2b-f2a05496a4e1

## Kritischer Entwicklungspfad
#14 Bootstrap → #15 Propagation → #16 Sync → #17 Fork Resolution → #18 Docker → #8 Multi-Node LIVE

## 🤖 Bekannte Base44-Superagent-Instanzen (5)
| # | App-ID | Git-Identitaet | Rolle | Signiert? |
|---|--------|----------------|-------|-----------|
| 1 | `69c1e0c577ccf6c45a27a480` | Michael Wroblewski (+ Tag) | Compliance (unverifiziert, kein Commit-Nachweis) | ✅ |
| 2 | `6a2756186106d6f0fbb105b5` | Michael Wroblewski (+ Tag) | Sync/Cleanup/Governance (dieser Agent) | ✅ |
| 3 | `6a27614c7219ab1e4f951842` | Aurora (MasterBrain) `<aurora@a-townchain.dev>` | ATCLang-Parser, Reality-Checks | ✅ (meist) |
| 4 | `6a0a3f408dced6c5ca7506ef` | Michael Wroblewski (+ Tag) | Reality-Check/Audit | ✅ |
| 5 | ⚠️ unbekannt | `Aurora-Bot <aurora@base44.ai>` | Taeglicher Wiki-Kapitel-Sync | ❌ unsigniert |

> Vollstaendiges Register mit Details: `docs/AGENT_COORDINATION.md`

## Sync-Konfiguration
- **Schedule:** täglich 08:05 Europe/Berlin
- **Agent:** Aurora (Base44 Superagent)
- **Script:** .agents/skills/kai_os_sync/scripts/master_sync.py
- **Version:** v3.0

---

## REPOSITORY-BAUHIERARCHIE (AD-026, 07.09.2026 — VERBINDLICH)

Die 22 Repos bauen SEQUENZIELL aufeinander auf (ein Layer startet nach
Gate-Erreichung des vorherigen; Wiki-Hub parallel):

[L0] atclang (Sprache/ATC-IR/Bytecode/ATVM, Gates G0-G19)
 → [L1] atc-shivacore (Kernel, SC-001…SC-013)
 → [L2] aurora-ai (Rust Core + Python AI-Layer, Kernel-Event-Bridge)
 → [L3] a-townchain (Blockchain L1, Chain-ID 658467)
 → [L4] globus-os (Userspace-OS auf ShivaCore)
 → [L5] atc-node, atc-contracts, atc-wallet, atc-sdk, atc-storage,
       atc-compute, atc-oracle, atc-indexer, atc-explorer, atc-interop,
       atc-mining, atc-marketplace, atc-launchpad (Blockchain-Services)
 → [L6] genesis-engine → genesis-chronicles
 → [L7] a-townchain-os (DIESES Repo: Integration aller Layer, AD-017)
[Hub] a-townchain-os-docs (Wiki/Vault, parallel)

Regel: Rebuild eines Layers erst nach Freeze/Gate des vorherigen.
Details: a-townchain-os-docs/docs/REPOSITORY_MAP.md (AD-026-Tabelle).

---

## LAUFFÄHIGKEITS-ROADMAP (AD-027, 07.09.2026 — VERBINDLICH)

Jede Stufe muss ein lauffähiges Inkrement liefern (Run-Kriterium mit Nachweis):
M1 Sprache läuft (atclang, G1-G6) → M2 Kernel läuft (Vault-Restauration,
674/674 + Boot L0-L10) → M3 KI läuft (aurora-ai, Kernel-Event-Bridge) →
M4 Blockchain läuft (2 Nodes, Chain-ID 658467, Contract auf ATVM) →
M5 OS läuft (globus-init-Bootchain) → M6 Dienste laufen (node→wallet→sdk→…) →
M7 Spiel läuft (genesis-engine→chronicles, NFT auf Chain) →
M8 Ökosystem läuft (dieses Repo: Launch-Stack, docker-compose healthy).
Volltext: a-townchain-os-docs/docs/roadmap/LAUFFAEHIGKEITS_ROADMAP.md
