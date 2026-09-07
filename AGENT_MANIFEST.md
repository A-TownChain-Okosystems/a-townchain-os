# AGENT_MANIFEST.md
> Letzte Aktualisierung: 2026-09-07 18:55 UTC | Aurora Master Sync v3.1.7 | 26-Repo-Stand (AD-016–AD-046) | Rollout auf alle 26 Repos

## Repositories (26 aktive — AD-016 + AD-024 + atc-standards + AD-043/044/045 + SCR-0005/AD-046)
### Kern-Plattform (9)
| Repo | Rolle | Zustand (07.09.2026) |
|------|-------|---------------------|
| [a-townchain-os-docs](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs) | **DOCS-HUB** — Wiki, DECISIONS_REGISTER (AD-001…039), Roadmaps, Audits | ✅ aktiv |
| [atc-standards](https://github.com/A-TownChain-Okosystems/atc-standards) | **KANONISCHE Standards-Heimat** (AD-030): ATC-STD-000…203 + ATC-STD-300 (DTC), Registry, Validator | ✅ ATC-STD-000 v1.1.0 APPROVED |
| [atclang](https://github.com/A-TownChain-Okosystems/atclang) | ATCLang 1.0 (Rust-first, AD-021/022), Gates G0-G19 | ✅ G1+G2 bestanden, Suite 126/126 (Python-Baseline; Rust-first G0 ausstehend) |
| [atc-vm](https://github.com/A-TownChain-Okosystems/atc-vm) | A-TownChain Virtual Machine — verifizierte Bytecode-Ausfuehrung (AD-043) | 🆕 R1-Skeleton (07.09.) |
| [atc-algorithm](https://github.com/A-TownChain-Okosystems/atc-algorithm) | ATC-Algorithmus — Hybrid Consensus PoH+PoS+PoW (AD-044) | 🆕 R1-Skeleton (07.09.) |
| [atc-zkp](https://github.com/A-TownChain-Okosystems/atc-zkp) | ATC ZKP-Layer — Zero-Knowledge Proof Layer, Verifikationsschicht L1↔Apps (AD-045, ATC-STD-ZKP-001…010) | 🆕 R1-Skeleton (07.09.) |
| [a-townchain-os](https://github.com/A-TownChain-Okosystems/a-townchain-os) | Monorepo — NUR Integration (AD-017: `scripts/sync_modules.py`) | ✅ 731/731 Workspace-Tests |
| [atc-shivacore](https://github.com/A-TownChain-Okosystems/atc-shivacore) | ShivaCore Microkernel (AD-012/013) + Service-Space (AD-028) | ✅ 674/674 Tests, Boot L0-L10 (M2-Gate erfüllt) |
| [a-townchain](https://github.com/A-TownChain-Okosystems/a-townchain) | Chain-Protokoll & Bibliothek (SCR-0005 A/AD-046): State, Tx, Orchestrierung; Chain-ID 658467 | ✅ vault-restauriert (6 Module) |
| [globus-os](https://github.com/A-TownChain-Okosystems/globus-os) | OS-Produkt (Userspace auf ShivaCore) | ✅ vault-restauriert (10 Module) |
| [aurora-ai](https://github.com/A-TownChain-Okosystems/aurora-ai) | AI-Produkt: Rust Core + Python AI-Layer (AD-021) | ✅ vault-restauriert (6 Module) |
| [genesis-engine](https://github.com/A-TownChain-Okosystems/genesis-engine) | Game-Engine-Produkt (L6) | ✅ vault-restauriert |

### Vertikale Repos (14, AD-024)
| Repo | Priorität | Inhalt |
|------|-----------|--------|
| [genesis-chronicles](https://github.com/A-TownChain-Okosystems/genesis-chronicles) | P1 | NFT-Game „Genesis Chronicles" (ex-shivamon, AD-025) | ✅ restauriert |
| [atc-contracts](https://github.com/A-TownChain-Okosystems/atc-contracts) | P0 | Smart-Contract-Standards + .atc-Referenzverträge | ✅ restauriert |
| [atc-sdk](https://github.com/A-TownChain-Okosystems/atc-sdk) | P0 | Developer Platform | ✅ restauriert |
| [atc-wallet](https://github.com/A-TownChain-Okosystems/atc-wallet) | P0 | Wallet (ATC+32-Adressen, BIP44 m/44'/658467', AD-042) | ✅ restauriert |
| [atc-explorer](https://github.com/A-TownChain-Okosystems/atc-explorer) | P1 | Block Explorer (TypeScript) | ✅ restauriert |
| [atc-indexer](https://github.com/A-TownChain-Okosystems/atc-indexer) | P1 | Indexing/Analytics | ✅ restauriert |
| [atc-interop](https://github.com/A-TownChain-Okosystems/atc-interop) | P1 | Bridges (ATC-09) | ✅ restauriert |
| [atc-marketplace](https://github.com/A-TownChain-Okosystems/atc-marketplace) | P2 | NFT/Asset-Marktplatz | ✅ restauriert |
| [atc-node](https://github.com/A-TownChain-Okosystems/atc-node) | P0, S4 | Full-Node-Binary & Runtime (SCR-0005 A/AD-046): baut auf a-townchain + atc-algorithm + atc-vm auf | 🔲 Skelett (R1) |
| [atc-storage](https://github.com/A-TownChain-Okosystems/atc-storage) | P2 | Storage-Schicht (ContentCap-Fundament) | 🔲 Skelett |
| [atc-compute](https://github.com/A-TownChain-Okosystems/atc-compute) | P2 | Compute-Schicht | 🔲 Skelett |
| [atc-oracle](https://github.com/A-TownChain-Okosystems/atc-oracle) | P2 | Oracle (ATC-10) | 🔲 Skelett |
| [atc-mining](https://github.com/A-TownChain-Okosystems/atc-mining) | P1 | Mining-Stack | 🔲 Skelett |
| [atc-launchpad](https://github.com/A-TownChain-Okosystems/atc-launchpad) | P2 | Token/NFT-Launchpad | 🔲 Skelett |

> **Alle 25 Repos (ohne atc-standards): GATE PASS nach ATC-STD-201/202/203
> (AD-039, 07.09.)** — governance-ci.yml auditiert jeden Push/PR.
> **Chain-ID:** 658467 (AD-004 RESOLVED). **Mainnet-Launch: per AD-023 offen.**

## GOVERNANCE-STAND (07.09.2026 — 41 APPROVED + NEU: ATC-AAS + ATC-ENT-BLÖCKE)
- **41 Standards APPROVED** (normativ): Verfassung ATC-STD-000 v1.2.0,
  201-204, BUG-001..004, NET-001..008, 100, 300, ZKP-001..010,
  AI-DEV-001..012 (Familie komplett).
- **NEU: ATC-AAS-Block** (20:07 UTC+2, Owner-Entwurf): 25 Agenten-
  Standards ATC-AAS-001..025 CANDIDATE (P0/P1/P2), erweitert AI-DEV
  ohne Duplikate; Freigabe §9 ausstehend (Todo #113) inkl. SCR-0006.
- **NEU: ATC-ENT Enterprise Standards Layer** (20:11 UTC+2,
  Owner-Entwurf): 15 Standards ATC-ENT-001..015 CANDIDATE — Lage
  ÜBER den technischen Familien, UNTERHALB der Verfassung:
  Unternehmens-Governance, Rollen (ROLE-XXX), Entscheidungsmanagement
  (DEC-NNNN, Kernregel: Verantwortlicher/Status/Begründung/Historie),
  Delegation, Richtlinien (POL), Interessenkonflikte, Eskalation (E1-E4),
  Organisationsstruktur (13 Einheiten), Repository Governance
  (REPO-NNNN), Change-Pipeline, Risiko-Management (RISK-NNNN),
  Consistency Gate, KPIs, Audit (WHO/WHAT/WHEN/WHERE/WHY/VERSION/
  RESULT), Definition of Done. Aufbau ohne Duplikate: Rollen bauen auf
  Verfassung §14.1 auf; Agenten-Governance bleibt bei AI-DEV/AAS;
  AD-Mandate grandfathered als DEC-Records. Schema-Erweiterung: roleId,
  decisionId, riskId, repoId, orgUnitId, escalationId.
- Registry: 81 Standards (41 approved, 50 candidate), Graph azyklisch,
  Versionshistorie 81/81.
- **NEU (07.09.2026 20:07 UTC+2): Standardblock ATC-AAS — AI Agent
  Standards** (Owner-Entwurf): 25 Standards ATC-AAS-001…025 als CANDIDATE
  in atc-standards/standards/aas/. P0: Identity, Permission, Scope,
  Discovery, Task, Workflow, Evidence, Verification, Security, PR, Human
  Approval, Audit Trail. P1: Context, Change, Conflict Resolution, Handoff,
  Failure, Versioning, A2A Protocol, Repository Manifest. P2: Quality/KPIs,
  Roles. Erweitert die freigegebene AI-DEV-Familie per Cross-Referenz
  (keine Duplikate). Freigabe §9 ausstehend; SCR-0006 (Commit-Typ-Set)
  mitentscheiden. Nach APPROVED: Repo-Manifeste (.github/ai/agent.yaml) je
  R2+-Repo bis 07.10.2026 (mit Task #111 verzahnt).
- **41/41 Standards APPROVED** (Owner-Sammelfreigabe „alle restlichen
  offenen Punkte", 07.09.2026 20:05 UTC+2): Verfassung ATC-STD-000 v1.2.0,
  Repository-Standards 201/202/203/204, BUG-001..004, NET-001..008,
  ATC-STD-100, ATC-STD-300, ZKP-001..010 sowie die komplette AI-DEV-Familie
  001..012 (8 neue Standards 002/003/005/006/008/010/011/012 mit erstellt).
  SCR-0001/0004 finalisiert, F-001/F-004 RESOLVED.
  Kanonisch: atc-standards/approval/APPROVAL-DECISION-2026-09-07-ALL-REMAINING.md.
  Verbleibende Owner-Aktion: F-009/F-010 (workflow-Scope-Token für CI-Fix).
  Übergangsfristen bis 07.10.2026: Commit-Trailer, Agent-Manifeste +
  AGENTS.md, Interface-Test-Suiten IFC-0001..0010.
- **NEU APPROVED (07.09.2026, 19:55 UTC+2, Owner-Direktfreigabe):**
  ATC-STD-204 (Dependency & Interface Standard) + ATC-STD-AI-DEV-Familie
  001 (Agent Identity & Workflow, Dach), 004 (Task Management),
  007 (Git Commit/PR), 009 (Audit Trail) — alle v1.0.0, normativ in Kraft.
  Kanonisch: atc-standards/approval/APPROVAL-DECISION-2026-09-07-204-AI-DEV.md.
  Übergangsfristen bis 07.10.2026: Commit-Trailer statt [agent:]-Tag
  (AI-DEV-007 §1), Agent-Manifeste (.github/ai/) + AGENTS.md in R2+-Repos,
  Interface-Test-Suiten IFC-0001..0010 (ATC-STD-204 seed → active).
- **ATC-STD-000 Verfassung v1.2.0 APPROVED** (Owner-Freigabe „Alles
  freigeben", 07.09.2026 20:00 UTC+2): §37 ID-Allokation (SCR-0001), §38
  Security (F-004). Gültige Verfassungsfassung; Änderungen nur via SCR
  (§30). SCR-0003 (Branch Protection, Option B) final akzeptiert — physisch
  verifiziert (Protected main aktiv). V-16-WARN akzeptiert;
  Conventional-Commits-Types normativ über AI-DEV-007 §1.
  Kanonisch: atc-standards/approval/APPROVAL-DECISION-2026-09-07-000-v1.2.0.md.
- **Naming (§7, normativ + CI-durchgesetzt):** IDs min. 3-stellig, immutable,
  Status nie in der ID; neue Repos atc-<domain>-<component>; Regeln NUR aus
  naming-conventions.schema.json (Validator S-16, Duplicate Detection S-17).
- **SCR-Prozess (change-requests/):** SCR-0001 (ID-Allokation, PENDING),
  SCR-0002 (OBSOLETE), SCR-0003 (Branch-Absicherung, Owner-Option A/B),
  SCR-0004 (Rollenmodell, PENDING).
- **Rollenregel:** Owner = Approver; Agenten = Autor/Reviewer/Executor,
  NIE Approver.
- **Prompt Engineering:** ATC-SPEC-001 (APOS/ACE) — deterministische
  Agent-Aufgaben auf Action/Process-Ebene mit Verifikation.

## BAUHIERARCHIE (AD-026, verbindlich) & ROADMAP (AD-027, verbindlich)
```
[L0] atclang → [L1] atc-shivacore → [L2] aurora-ai → [L3] a-townchain
 → [L4] globus-os → [L5] 13 Blockchain-Services → [L6] genesis-engine →
 genesis-chronicles → [L7] a-townchain-os (Integration, AD-017)
[parallel] a-townchain-os-docs (Docs-Hub) · atc-standards (Norm)
```
Lauffähigkeits-Roadmap M1-M8 (jede Stufe = lauffähiges Inkrement):
M1 Sprache (G1 ✅ → G2 offen) → M2 Kernel (✅ 674/674 + Boot) → M3 KI →
M4 Blockchain (2 Nodes, 658467, Contract auf ATVM) → M5 OS → M6 Dienste →
M7 Spiel (NFT auf Chain) → M8 Ökosystem (Launch-Stack).
Volltext: docs/roadmap/LAUFFAEHIGKEITS_ROADMAP.md ·
Regel: Layer startet erst nach Gate des vorherigen.

## Integrationen (17 aktiv)
| Integration | Status | Zweck |
|-------------|--------|-------|
| GitHub | ✅ | Code + Docs Hosting (verbindliche Primär-Quelle) |
| Notion | ✅ | Roadmap + Protokolle |
| Google Sheets | ✅ | Dashboard + Metriken |
| Google Docs/Slides/Calendar/Drive/Analytics/BigQuery/Search Console/Tasks/Meet/Classroom | ✅ | Reports/Metriken/Sprints/Archiv |
| Gmail | ✅ | Status-Reports (NUR SENDEN) |
| Microsoft Outlook/Teams/OneDrive | ✅ | Reports/Kommunikation/Backup |
| Hugging Face | ✅ | KI-Modelle |

## Google Sheets Dashboard
ID: 1xR5c24NrtYC58OsGrLaUHkQUiL_O6eYVyx8KmFcvBD4
URL: https://docs.google.com/spreadsheets/d/1xR5c24NrtYC58OsGrLaUHkQUiL_O6eYVyx8KmFcvBD4

## Notion
- Roadmap: 373b826d-b85c-8125-ba83-f04995191bf0
- Tagesprotokoll: 37bb826d-b85c-81c4-bdd4-cfc0dc74de7e
- Live-Status: 379b826d-b85c-81f1-9b2b-f2a05496a4e1

## Kritischer Entwicklungspfad (AD-027)
M1 G2 (Semantics) → M3 KI (Kernel-Event-Bridge) → M4 Blockchain (2 Nodes
Sync) → M5 OS (globus-init-Bootchain) → M6 Dienste → M7 Spiel → M8 Stack.
Parallel: Issue #69 (Dependabot), #70 Validators, #71 Genesis Block.

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
- **Version:** v3.1
