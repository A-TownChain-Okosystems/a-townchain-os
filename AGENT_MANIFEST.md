# AGENT_MANIFEST.md
> Letzte Aktualisierung: 2026-08-04 12:28 UTC+2 | Aurora Parser-Sprint Update

## Repositories
- **Code (Monorepo):** https://github.com/A-TownChain-Okosystems/a-townchain-os
- **Kernel (ShivaCore):** https://github.com/A-TownChain-Okosystems/atc-shivacore
- **Parser (ATCLang):** https://github.com/A-TownChain-Okosystems/atc-atclang
- **Weitere atc- Repos:** atc-blockchain, atc-backend, atc-gateway, atc-frontend,
  atc-aistudio, atc-mobile, atc-shivacore-tools, atc-windows-edition, atc-linux-edition,
  atc-genesis-engine

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

| # | App-ID | Rolle | Letzte Aktivität | Repos | Commits | Signiert? |
|---|--------|-------|------------------|-------|---------|-----------|
| 1 | `69c1e0c577ccf6c45a27a480` | **ShivaCore Kernel-Dev** — K-Sprint 21-29 (Compiler-Fixes, Warning-Eliminierung, Security Audit, 712/712 Tests grün) | 2026-08-04 09:53 | atc-shivacore | 16 | ✅ |
| 2 | `6a2756186106d6f0fbb105b5` | **Sync/Cleanup/Governance** — Monorepo-Aufräumarbeiten, Wiki-Sync, REALITY_STATUS.md-Pflege, Cross-Repo-Konsistenz | 2026-08-04 12:00 | a-townchain-os | 14 | ✅ |
| 3 | `6a27614c7219ab1e4f951842` | **MasterBrain/Reality-Checks** — ATCLang-Parser-Audits, REALITY_STATUS.md-Verifizierung, Sprint-Doku | 2026-08-04 10:00 | a-townchain-os, atc-shivacore | 7 | ✅ |
| 4 | `6a0a3f408dced6c5ca7506ef` | **ATCLang Parser-Dev** — 14 Syntax-Fixes (if let, closures, unit type, or-pattern, etc.), 208/221 .atc files (94%), ShivaCore K0-K20 | 2026-08-04 10:12 | a-townchain-os, atc-atclang | 11 | ✅ |
| 5 | ⚠️ unbekannt | `Aurora-Bot <aurora@base44.ai>` — Tägl. Wiki-Kapitel-Sync | unklar | a-townchain-os | ? | ❌ unsigniert |

### Agenten-Aktivitäts-Summary (Stand 04.08.2026)

**Agent #1** (`69c1e0c5`) — **AKTIV, HAUPTKERNEL-DEV**
- K-Sprint 21-29 in atc-shivacore abgeschlossen
- 142 Compile-Fehler behoben, 497 Warnings eliminiert → 0/0
- 712/712 Tests grün (von 441 → 712, +271 neue Tests)
- Security Audit (security.rs + security_audit.rs)
- ⚠️ Früher als "unverifiziert" gelistet — **korrigiert**: 16 Commits nachgewiesen

**Agent #2** (`6a2756186106`) — **AKTIV, MONOREPO-SYNC**
- 14 Commits in a-townchain-os (letzte 30)
- Wiki-Sync, Status-Dokumentation, Cleanup
- REALITY_STATUS.md Pflege und Cross-Repo-Konsistenz

**Agent #3** (`6a27614c7219`) — **AKTIV, REALITY-CHECKS**
- REALITY_STATUS.md erstellt und verifiziert (03.08.2026)
- ATCLang-Parser-Audits, Sprint-Dokumentation
- 7 Commits in letzten 30 (a-townchain-os + atc-shivacore)

**Agent #4** (`6a0a3f408dced6c5`) — **AKTIV, PARSER-DEV** (dieser Agent)
- 14 Syntax-Fixes im ATCLang Parser → 208/221 (94%) parse OK
- ATCLang Parser in atc-atclang gepusht (2 Commits, 58.241 bytes)
- REALITY_STATUS.md aktualisiert (Sprint 2.1 → 94%)
- Frühere Session: ShivaCore K-Sprint 0-20, 441 Tests, 63 Dateien Cleanup

**Agent #5** (Aurora-Bot) — **STATUS UNKLAR**
- Git-Identität `Aurora-Bot <aurora@base44.ai>`
- Ursprünglich für täglichen Wiki-Sync, aktuelle Aktivität unklar
- Nicht signiert (kein Base44 App-ID zugeordnet)

## ⚠️ Bekannte Sync-Probleme
1. **Parser-Divergenz:** Monorepo-Parser (64.418 bytes, 221/221 = 100%) ≠ atc-atclang-Parser (58.241 bytes, 208/221 = 94%). Besserer Parser wurde nicht zurück zu atc-atclang synchronisiert.
2. **`docs/AGENT_COORDINATION.md` fehlt** — referenziert aber 404. Sollte neu erstellt oder Referenz entfernt werden.
3. **`docs/AGENT_POLICY.md` fehlt** — ebenfalls 404. Regeln jetzt in `AGENT_MASTERRULES.md` konsolidiert.

## Sync-Konfiguration
- **Schedule:** täglich 08:05 Europe/Berlin
- **Agent:** Aurora (Base44 Superagent)
- **Script:** .agents/skills/update-roadmap/scripts/run.py
- **Version:** v3.1 (04.08.2026 — Parser-Sync-Problem dokumentiert)

---
*Stand: 04.08.2026 12:28 (Europe/Berlin) · Agent #4 (`6a0a3f408dced6c5ca7506ef`)*
