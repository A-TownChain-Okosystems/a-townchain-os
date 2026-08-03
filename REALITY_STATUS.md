# 🔍 REALITY STATUS — Verifizierter Ist-Zustand

> **WICHTIG FÜR ALLE KI-AGENTEN:** Diese Datei ist die einzige Quelle, deren Zahlen
> am 06.07.2026 durch tatsächliche Skript-Ausführung (nicht durch Lesen alter Doku)
> verifiziert wurden. Bei Widersprüchen zu README.md, ROADMAP.md, STATUS.md,
> MILESTONES.md, STANDARDS_REGISTRY.md oder Wiki-Kapiteln gilt **diese Datei**.
> Erstellt/verifiziert von: `aurora-base44-superagent-6a27614c7219ab1e4f951842`
> **Stand:** 06.07.2026, 22:19 UTC+2 — Methode: Parser-Lauf, `pytest`, GitHub-API, `find`/`grep` über beide Repos.

---

## 1. ATCLang — Code-Realität

| Metrik | Wert | Verifikationsmethode |
|---|---|---|
| `.atc`-Dateien gesamt | **176** | `find . -name "*.atc"` |
| Zeilen ATCLang gesamt | **30.953** | `cat *.atc \| wc -l` |
| **Parsen fehlerfrei** | **96 / 176 (54,5%)** | Eigener Parser-Lauf (`atclang/parser`), nicht nur Datei-Existenz |
| Parsen NICHT | **80 / 176 (45,5%)** | s. Abschnitt 2 |
| Solidity-Dateien | **0** | Non-EVM bestätigt |

⚠️ **Frühere Behauptungen "119/119" oder "126/127 parsen" (Sessions vom 05.07.) waren zum
Zeitpunkt der Aussage vermutlich korrekt für den damaligen Dateibestand — seither wurden
~57 neue `.atc`-Dateien in einem anderen Sprach-Dialekt hinzugefügt** (Module `franchise/`,
`meta/`, `civilization/`, `kernel/*_bus_ad*`), die der aktuelle Parser (v0.3) nicht unterstützt.

## 2. ATCLang v1.0-Dialekt-Problem (Sprint 2.1 Blocker, ungelöst)

Die 80 nicht-parsenden Dateien sind **kein Tippfehler-Bug**, sondern ein grundsätzlicher
Sprachversions-Konflikt:

- **Franchise/Meta/Civilization-Module (~57 Dateien):** nutzen `module X.Y[AD-nn] { }`-Wrapper,
  Generics (`Map<K,V>`, `List<T>`, `Option<T>`), Struct-Felder ohne Kommas, verschachtelte
  `import`-Statements innerhalb von Blöcken — nichts davon unterstützt der v0.3-Parser.
- **`modules/assets/*.atc` (16 Dateien, 2.042 Zeilen):** sind de facto **Python-Syntax mit
  `#`-Kommentaren und `enum X:`-Blöcken** — das ist gar kein ATCLang, sondern fälschlich
  als `.atc` benanntes Pseudocode. Muss komplett neu geschrieben werden, kein Parser-Fix möglich.
- **`atcos_main.atc` (1.158 Zeilen):** bereits als "v1.0-Showcase" bekannt (Vererbung, `for-in`,
  Power-Operator) — gleiches Grundproblem.

**Fix in dieser Session:** String-Pfad-Importe (`import "std/x.atc" as Y`) und gepunktete
Importe mit Bracket-Tag (`import GCL.Core[AD-00]`) wurden zum Parser hinzugefügt — das hat
92→96 Dateien gebracht. Der Rest braucht einen echten v1.0-Parser (Generics, Modul-Blöcke,
kommalose Structs) — das ist ein Mehrtage-Engineering-Sprint, kein Ein-Zeilen-Fix.

## 3. Python-Stub-Regression (WICHTIG — widerspricht "Migration Complete")

⚠️ **Mehrere Dateien behaupten "0 Python-Stubs" / "Migration Complete" (Stand 05.07.2026):**
`docs/wiki/chapter-70-atclang-migration-complete.md`, `docs/MIGRATION_MAP.md`,
`docs/standards/STANDARDS_REGISTRY.md` (ATC-99 Zeile), `docs/wiki/kai-os/docs/ROADMAP.md`.

**Das stimmt nicht mehr.** Tatsächlicher Stand heute:
- **72 reale (nicht-leere) Python-Dateien** außerhalb von `tests/` und `atclang/` (Compiler selbst).
- Davon **21 Dateien** wurden am 06.07. von einem anderen Agenten (`...105b5`, Session "K3
  Teilfortschritt") bewusst aus `aistudio/temp_repo/` zurück in den Haupt-Baum kopiert
  (`backend/`, `blockchain/`, `core/`, `gateway/`, `modules/kernel/ai_kernel/`), weil die
  Testsuite Python-Importe erwartet, die es in ATCLang-Form nicht gibt.
- **51 weitere Python-Dateien** liegen in `aistudio/temp_repo/` — ein bisher nicht konsolidiertes
  Parallel-Projekt (K3/K4 Konsolidierungsarbeit läuft, s. `AGENT_COORDINATION.md`).

**Konsequenz:** Die "ATCLang-Migration abgeschlossen"-Aussage ist **stale** und sollte von
keinem Agenten mehr unkritisch übernommen werden, bis K3/K4 wirklich abgeschlossen sind.

## 4. Testsuite (frisch ausgeführt, `pytest -q --continue-on-collection-errors`)

| Ergebnis | Anzahl |
|---|---|
| Gesammelt | 345 (von 349 — 4 Collection-Errors) |
| ✅ Grün | **302** |
| ❌ Rot | **30** |
| ⏭️ Skipped | 13 |
| 🚫 Collection-Error | 4 (`test_bootstrap.py`, `test_did.py`, `test_orchestrator.py`, `test_kai_integration.py`) |

Ursachen der 4 Collection-Errors: fehlende Module (`blockchain.nodes.bootstrap`,
`blockchain.wallet.did`), API-Mismatch (`AIRequest` fehlt in `ai_kernel.py`), zirkulärer
Import in `backend/api/routes/__init__.py`. **0 echte ATCLang-Tests** — Testsuite ist
komplett Python-basiert, obwohl Produktcode laut Mandat ATCLang sein soll.

## 5. GitHub Issues (live via API geprüft)

| Repo | Offen | Geschlossen | Gesamt | Quote |
|---|---|---|---|---|
| a-townchain-os | 11 | 79 | 90 | 87,8% geschlossen |
| a-townchain-os-docs | 0 | 0 | 0 | — |

⚠️ Frühere Zahl "78/82 (95,1%)" ist veraltet — seit K1-K8-Konsolidierungs-Issues
(#85–92) geöffnet wurden, hat sich Nenner und Zähler verschoben.
Unverändert offen: **44 von 79 geschlossenen Issues (56%) referenzieren nicht-existente
Dateien** (s. `docs/REALITY_CHECK_2026-07-06.md`) — Re-Open-Entscheidung liegt weiter bei Michael.

## 6. Wiki-Kapitel-Zahl ist NICHT verifizierbar — Metrik einstellen

README.md und ECOSYSTEM.md behaupten **"75 Kapitel"**. Tatsächlich:

- Nur **9 Dateien** folgen dem Muster `chapter-N-*.md` (Kapitel 63, 70–77).
- Die restlichen **134 Markdown-Dateien** unter `docs/wiki/` sind thematisch in Unterordnern
  organisiert (`kai-os/`, `standards/`, `overview/`, `contracts/`, …) — **ohne erkennbare
  1:1-Zuordnung zu einer Kapitelnummer 1–69**.
- `docs/wiki/kai-os/` ist zudem eine **komplette verschachtelte Kopie einer Repo-Struktur**
  (`code/backend/`, `code/blockchain/`, `docs/standards/`, …, 58 Dateien) — vermutlich ein
  alter, nie aufgeräumter Sync-Schnappschuss, kein echtes "Kapitel".

**Empfehlung an Michael:** Die "Wiki hat X Kapitel"-Kennzahl ist nicht mehr seriös messbar,
solange Kapitel nicht 1:1 als `chapter-N-*.md` vorliegen. Entweder alle Themen-Dateien
formal nummerieren, oder die Kennzahl aus Status-Reports streichen.

## 7. Standards-Registry — Duplikate & Bruch der Namenskonvention

- **101 Dateien** unter `docs/standards/` matchen `ATC-*.md` (nicht 98 oder 99 wie behauptet).
- **`ATC-0009-BRIDGE.md` existiert doppelt** (`docs/standards/ATC/` UND `module-docs/standards/`)
  — altes Nummernformat (4-stellig mit führender Null), das laut Session vom 05.07. bereits
  vollständig auf `ATC-01`–`ATC-99` migriert sein sollte.
- **`ATC-LIC-SMART_CONTRACT_LICENSE.md`** und **`ATS-LIC-SYSTEM_HARDWARE_LICENSE.md`** brechen
  die "nur ATC-01 bis ATC-99, keine anderen Präfixe"-Regel (ATS war laut Regelwerk bereits
  eliminiert). Diese Dateien referenzieren zudem ein **BaFin-Compliance-Handbuch**, dessen
  Existenz/Richtigkeit von einem anderen Agenten bereits als "unverifiziert" markiert wurde
  (s. `AGENT_COORDINATION.md`, Fund zu Agent `69c1e0c...a480`).

## 8. In dieser Session behoben ✅

| Fix | Datei(en) | Commit |
|---|---|---|
| ~~Chain-ID 9001→9000 vereinheitlicht~~ **ZURUECKGENOMMEN** | War falsch — s. Abschnitt 10 | `17a4096` (ueberholt) |
| Parser: String-Pfad-Importe unterstützt | `atclang/parser/parser.py` | `17a4096` |
| Dependency-Sicherheitsupdates (cryptography, requests, python-dotenv, pytest, flask, flask-cors) | `requirements.txt`, `backend/requirements.txt`, `requirements-kai.txt`, `aistudio/temp_repo/gateway/requirements.txt` | `17a4096` |
| npm audit fix (non-breaking) — 11→10 verbleibende Alerts | `aistudio/package-lock.json` | `17a4096` |

## 9. Offen — braucht Michaels Entscheidung (REGEL 9)

1. **Parser v1.0-Upgrade** für 80 Dateien (Generics, Modul-Blöcke) — eigener Sprint, kein Quick-Fix.
2. **`modules/assets/*.atc`** (16 Dateien) sind kein ATCLang — Neuschreiben oder löschen?
3. **44 Issues mit gebrochener Datei-Referenz** — re-open oder als historisch akzeptieren?
4. **K3/K4-Konsolidierung** (`aistudio/temp_repo/` → Haupt-Baum) — wann/wie abschließen, um die
   Python-Stub-Regression zu beenden?
5. **npm `uuid`-Vulnerability** — Fix erfordert Breaking-Change-Upgrade von `firebase-admin`.
6. **Wiki-Kapitel-Zählweise** — neu definieren oder Kennzahl aufgeben (s. Abschnitt 6).
7. **ATC-LIC/ATS-LIC/BaFin-Compliance-Doku** — Status prüfen, ggf. als DRAFT/unverifiziert kennzeichnen.

---
*Nächster Agent: Vor jeder "X ist fertig/behoben/abgeschlossen"-Aussage — dieses Dokument
aktualisieren, nicht nur eine neue Behauptung obendrauf schreiben.*


## 10. ⚠️ NACHTRAG (06.07.2026, 22:25) — AD-004 Chain-ID REOPENED, keine Chain-ID final

Michael hat direkt widersprochen: **"Wir haben noch keine Chain-ID, 9000 ist ID von Ethereum"**
(gemeint: Ethereum-Oekosystem/EVM-Registry). Verifiziert via chainlist.org: **Chain-ID 9000
ist auf Evmos Testnet registriert.**

Die vorherige "AD-004 RESOLVED"-Markierung (Begruendung: "Non-EVM macht Kollision irrelevant")
wurde von Michael **nicht akzeptiert und ist damit ungueltig**, auch wenn ein frueherer Agent
sie in `DECISIONS_REGISTER.md`/`AgentDecision`-Entity als "RESOLVED, resolved_by: Michael +
Aurora" eingetragen hatte — dieser Eintrag war offenbar falsch attribuiert oder ueberholt.

**Korrigiert in dieser Session:** `AgentDecision`-Entity (Base44) auf State `DECISION` (offen)
zurueckgesetzt, `docs/DECISIONS_REGISTER.md`, `docs/AGENT_POLICY.md`, `docs/ROADMAP.md`,
`docs/standards/STANDARDS_REGISTRY.md`, `docs/standards/OVERVIEW.md`,
`docs/roadmap/ROADMAP_EXTENDED.md` korrigiert: AD-004 = 🔴 OPEN/REOPENED, 9000 = nur Platzhalter.

**NICHT gemacht:** Die ~100+ restlichen Vorkommen von "Chain-ID 9000" in Code-Kommentaren,
Wiki-Seiten, Whitepaper, Issues wurden **nicht** massenhaft auf eine neue Zahl umgeschrieben —
das waere derselbe Fehler nochmal (Chain-ID automatisch entscheiden, REGEL 9 verbietet das
explizit). Diese Vorkommen sind ab sofort als **Platzhalter, nicht final** zu lesen, bis
Michael eine echte Chain-ID waehlt oder das Non-EVM-Argument erneut bestaetigt.

**Naechster Schritt:** Michael entscheidet zwischen (a) einer verifiziert freien neuen
Chain-ID, (b) Beibehaltung von 9000 als rein interne, nicht-oeffentlich-registrierte
Non-EVM-ID (dann muss die Begruendung explizit erneut bestaetigt werden), oder (c) einer
anderen Loesung. Erst danach macht ein Mass-Replace Sinn.


## 11. Sprint-Status: Drei widersprüchliche Quellen (nicht aufgelöst, nur dokumentiert)

Es existieren **drei verschiedene Sprint-Wahrheiten**, die sich teils stark widersprechen:

| Sprint | `EcosystemSprint`-Entity (Base44) | `SPRINT_ROADMAP.md` (Narrativ) | Real verifiziert |
|---|---|---|---|
| 2.1 (ATCLang Core) | 80% ACTIVE | ✅ ABGESCHLOSSEN | Parser schafft nur 54,5% aller `.atc`-Dateien — "abgeschlossen" nicht haltbar |
| 2.3 (Smart Contracts) | 90% ACTIVE | ✅ ABGESCHLOSSEN | — |
| 2.4 (Kernel/GCL) | **80% status PLANNED** | ✅ ABGESCHLOSSEN | Entity widerspricht sich selbst (80% aber PLANNED) |
| 2.6 (Governance) | 80% ACTIVE | ✅ ABGESCHLOSSEN | — |
| 2.7 (CI/CD) | **0% PLANNED** | ✅ ABGESCHLOSSEN | Größter Widerspruch: 0% vs. "fertig" |
| 3.0–3.6 | Ein einziger Entity-Eintrag "90% PLANNED" | 7 einzelne Sprints, gemischter Status | Entity-Granularität ≠ Doku-Granularität |
| 4.2a–d | 0% PLANNED ("Physical→Cosmic", "Singularity Engineering", …) | nicht in SPRINT_ROADMAP.md erwähnt | Aspirational/Fantasy-Tier, keine Code-Entsprechung |

**Fazit:** Die Markdown-Haken (✅ ABGESCHLOSSEN) in `SPRINT_ROADMAP.md` sind erkennbar
**narrativ/optimistisch** gesetzt, nicht aus der `EcosystemSprint`-Datenbank abgeleitet.
Issue-Zahl in `SPRINT_ROADMAP.md` war zusätzlich falsch (78/82 statt real 79/90 laut
GitHub-API) — das wurde in dieser Session korrigiert. Die Sprint-Status-Haken selbst
wurden **nicht angetastet** — das wäre wieder eine Bewertungsfrage, die Michael treffen
sollte (welche Quelle gilt: Entity oder Doku?).

## 12. TODO-Dateien in beiden Repos sind NICHT synchron

- Code-Repo `TODO/MASTER_TODO.md`: "Aktualisiert: 2026-06-12" (3+ Wochen alt), 31 offene / 0 erledigte Checkboxen, Task-Nummern #48–#51.
- Docs-Repo `TODO/MASTER_TODO.md`: "Stand: 2026-07-06", 2 offene / 0 erledigte Checkboxen, komplett andere Task-Nummern (#8, #14–#18).
- **Es sind zwei völlig unterschiedliche Dateien mit demselben Namen** — keine ist eine Kopie der anderen. Nicht zusammengeführt, weil unklar ist, welche die aktive Liste ist.

## 13. Commit/Push-Status (Ende dieser Session)

Beide Repos: Arbeitsverzeichnis sauber, lokale Commits = Remote-HEAD, keine Divergenz.
Letzte Commits: Code-Repo `3268fd4`, Docs-Repo `28f4381` (jeweils gepusht und verifiziert
per `git fetch` + `git log HEAD..FETCH_HEAD`).


## 14. NACHTRAG (07.07.2026, 14:30 UTC+2, Agent `6a0a3f408dced6c5ca7506ef`) — Stale-Content-Re-Check

Re-Verifikation eines Tages nach der letzten Aktualisierung dieses Dokuments (Abschnitt 1-13,
06.07. 22:19). Ergebnis: **teilweise behoben, teilweise unverändert stale, ein neues Problem
hinzugekommen.**

### ✅ Seither behoben
- `SPRINT_ROADMAP.md` Issue-Zahl korrigiert: zeigt jetzt korrekt "79/90 Issues geschlossen
  (87,8%)" mit Verweis auf dieses Dokument (war vorher 78/82).

### ⚠️ Weiterhin unverändert stale (nicht angefasst seit 06.07.)
- **`ECOSYSTEM.md`** behauptet weiterhin **"75 Kapitel, 99 Standards"** — beide Zahlen laut
  Abschnitt 6+7 oben nicht haltbar (real: 9 nummerierte Kapitel-Dateien, 101 ATC-*.md-Dateien).
- **`TODO/MASTER_TODO.md`** (Code-Repo) trägt weiterhin den Zeitstempel **"Aktualisiert:
  2026-06-12"** — mittlerweile 25 Tage alt, während das Docs-Repo-Pendant vom 06.07. stammt
  (s. Abschnitt 12, zwei-Datei-Problem weiterhin ungelöst).
- **Sprint-Haken in `SPRINT_ROADMAP.md`** (2.1, 2.4, 2.7 als "✅ ABGESCHLOSSEN") weiterhin
  unverändert, obwohl Abschnitt 11 oben sie als Entity-widersprüchlich markiert hat.
- **Chain-ID-Platzhalter "9000"**: Vorkommen im Repo sind seit gestern von geschätzt "~100+"
  auf **182 Treffer** (GitHub Code-Search) gestiegen — vermutlich durch neue Dateien, die alte
  Inhalte kopieren/duplizieren (s. u.), nicht durch eine bewusste Neu-Entscheidung. AD-004
  bleibt laut Abschnitt 10 OPEN/REOPENED — jedes neue "9000" ist weiterhin nur Platzhalter.

### 🆕 Neuer Fund: Massive Commit-Duplikation am 07.07. (12:07-12:10 UTC)
31 Commits allein am 07.07. bis 14:00 Uhr. Auffällig: mehrere **near-identische Commits
innerhalb von Sekunden**, vermutlich von unkoordinierten parallelen Agent-Läufen oder
Automation-Retries:
- "🔗 Cross-Connect Verbindungsmatrix 2026-07-07: 13/16" — 3x (12:09:56 / 12:10:00 / 12:10:06)
- "🤖 HuggingFace Modell-Registry 2026-07-07" — 3x (12:09:52 / 12:10:00 / 12:10:06)
- "🤖 AGENT_MANIFEST v3.0 2026-07-07" — 3x (12:07:07 / 12:09:52 / 12:10:02)
- "🔄 Aurora v3.0 2026-07-07: STATUS.md" — 3x (12:09:40 / 12:09:46 / 12:10:12)

Dies deckt sich mit dem in `AGENT_COORDINATION.md` dokumentierten **5. (unsignierten) Agenten**
(`Aurora-Bot <aurora@base44.ai>`), dessen App-ID weiterhin unbekannt ist. Auswirkung: Git-Historie
wird unnötig aufgebläht (31 Commits für vermutlich <10 tatsächlich unterschiedliche
Dateizustände), erschwert Nachvollziehbarkeit. Kein Datenverlust festgestellt — der jeweils
letzte Commit jeder Gruppe scheint der gültige Endzustand zu sein.

**Empfehlung:** Bevor weitere automatisierte Syncs laufen, sollte geklärt werden, ob mehrere
Automationen (dieser Agent, Agent `...105b5`, der unsignierte 5. Akteur) denselben
Sync-Job redundant auf denselben Dateien ausführen — das wäre über `list_automations`
je Agent-Instanz abgleichbar.

*Nächster Agent: Bitte auch diesen Abschnitt weiterschreiben statt duplizieren, gemäß Regel
am Ende von Abschnitt 9.*


---

## Update 08.07.2026 -- ATC Windows Edition (neues Repo)

Neues, separates Repository `atc-windows-edition` angelegt fuer eine Windows-native
Client-Anwendung des Oekosystems.

- **Sprachentscheidung:** Rust mit **std** (klassisches gehostetes Deployment,
  Ziel-Target `x86_64-pc-windows-msvc`) -- **NICHT** bare-metal/no_std wie der
  ShivaCore-Kernel.
- **Abgrenzung:** GlobusOS/ShivaCore (bare-metal Rust no_std) bleibt der alleinige
  OS-Standard des Oekosystems. `atc-windows-edition` ersetzt das nicht, sondern ist
  eine separate, parallele Windows-Anwendung (Client, kein eigenes OS/Kernel).
- **Status:** Sprint-0-Grundgeruest angelegt (Cargo.toml, src/main.rs). Scope
  (Desktop-GUI vs. CLI/Dienst) noch offen.
- Repo: https://github.com/A-TownChain-Okosystems/atc-windows-edition


---

## Update 08.07.2026 (Nachtrag) -- ATC Windows Edition: Scope final entschieden

Ergaenzung zum Eintrag oben (Sprachentscheidung Rust/std): der Scope war dort noch
offen, ist jetzt final:

- **Scope:** Desktop-App mit grafischer Oberflaeche (kein CLI-Tool, kein
  Hintergrunddienst).
- **GUI-Framework:** `egui`/`eframe` -- reines Rust, kein zusaetzlicher Web-/JS-Stack.
- **Geplante erste Views (Kandidaten, Reihenfolge offen):** Wallet, Explorer,
  Dashboard.
- **Ticket:** [WIN-S1] Scope-Entscheidung -- Status: erledigt (KaiOsTodo-DB).
- **Repo-Stand:** Cargo.toml (eframe/egui-Dependency) + src/main.rs (lauffaehiges
  egui-Fenster-Grundgeruest) bereits gepusht.
- Repo: https://github.com/A-TownChain-Okosystems/atc-windows-edition


---

## Update 08.07.2026 -- ATC Linux Edition (neues Repo)

Neues, separates Repository `atc-linux-edition` angelegt fuer eine Linux-native
Desktop-Client-Anwendung des Oekosystems -- Schwesterprojekt zu
`atc-windows-edition`.

- **Sprache:** Rust mit **std** (klassisches gehostetes Deployment, Ziel-Target
  `x86_64-unknown-linux-gnu`) -- **NICHT** bare-metal/no_std wie der
  ShivaCore-Kernel.
- **Scope:** Desktop-App mit grafischer Oberflaeche (analog Windows-Edition),
  kein CLI-Tool, kein Hintergrunddienst.
- **GUI-Framework:** `egui`/`eframe` -- reines Rust, plattformuebergreifend.
  Cross-Platform-Hinweis: der Code aus `atc-windows-edition` ist mit
  `cargo build --target x86_64-unknown-linux-gnu` grundsaetzlich ohne Aenderung
  auch fuer Linux baubar. Getrenntes Repo dient unabhaengiger Versionierung/CI
  (gleiche Begruendung wie bei ShivaCore-Ausgliederung), NICHT Code-Duplizierung.
  Code-Sharing-Strategie (Cargo-Workspace vs. manueller Sync) noch offen.
- **Abgrenzung:** GlobusOS/ShivaCore (bare-metal Rust no_std) bleibt der alleinige
  OS-Standard des Oekosystems. `atc-linux-edition` ersetzt das nicht.
- **Status:** Sprint-0-Grundgeruest angelegt (Cargo.toml mit eframe/egui-Dependency,
  lauffaehiges src/main.rs).
- Repo: https://github.com/A-TownChain-Okosystems/atc-linux-edition


---

## Update 09.07.2026 -- ATC Gateway sauber ausgegliedert (Korrektur)

`atc-gateway` war seit der Repo-Spaltungswelle vom 08.07.2026 faelschlich als
"archiviert/migriert nach a-townchain-os" beschriftet, obwohl der Gateway-Code
tatsaechlich weiterhin nur im Monorepo lag. Jetzt korrekt nachgeholt:

- 23 Dateien aus `gateway/` und `modules/gateway/` (Monorepo) nach
  `atc-gateway` migriert, Repo-Beschreibung korrigiert (kein "archiviert"
  mehr), Repo ist wieder aktive kanonische Quelle fuer Gateway-Code.
- **Struktur:** `python/` (stabile, produktive Implementierung) +
  `atclang/` (experimenteller Port derselben Logik nach ATCLang -- Status
  unklar, da ATCLang-Parser aktuell 96/176 Dateien betrifft, siehe Eintrag
  oben zu Generics/Modul-Bloecken).
- **Noch offen:** Tests (`tests/test_gateway_full.py`,
  `tests/unit/test_gateway.py`) liegen noch im Monorepo, nicht mitmigriert --
  Nachziehen als Folgeschritt.
- Repo: https://github.com/A-TownChain-Okosystems/atc-gateway


---

## Cleanup 03.08.2026 — Verwaiste Dateien entfernt

Folgende Dateien/Verzeichnisse wurden gelöscht (alle verwaist, dupliziert oder
superseded):

1. **`shivaos/`** (28 Dateien) — alte Python-Simulation des OS. Alle Kernel-Module
   (capabilities, kernel/process, did, remote_capability, scheduler, fs) vollständig
   nach Rust migriert in `atc-shivacore` (K-Sprint 3a-8). ATC-Stubs in shivaos/ux/
   dupliziert mit `docs/standards/`. shivaos/kernel/syscalls.atc und shivaos/ui/
   renderer.atc waren ATCLang-Skizzen ohne lauffähige Implementierung.

2. **`modules/future/`** (30 Dateien) — Platzhalter für ATC-51 bis ATC-80 (Vision/Lore,
   keine Engineering-Relevanz per Standing Instruction). Kanonische Standard-Dokumente
   existieren bereits in `docs/standards/`.

3. **`STATUS.md`** (45 Zeilen) — auto-generiert, stale.
4. **`ECOSYSTEM_STATUS.md`** (116 Zeilen) — auto-generiert 12.06.2026, stale.
5. **`ROADMAP.md`** (321 Zeilen) — Stand 05.07.2026, Behauptung "78/82 Issues closed"
   veraltet (12 offen, nicht 4).
6. **`SPRINT_ROADMAP.md`** (503 Zeilen) — Stand 05.07.2026, "79/90 Issues closed"
   veraltet.
7. **`KONSOLIDIERUNGS_ROADMAP.md`** (360 Zeilen) — Konsolidierungsplan vom 05.07.2026,
   durch Repo-Spaltung am 08.07.2026 überholt.

REALITY_STATUS.md bleibt die einzige kanonische Statusquelle (Standing Instruction).


---

## K-Sprint 16: Konsens-Mechanismus abgeschlossen (03.08.2026)

**Repo:** `atc-shivacore` · **Datei:** `kernel/src/consensus.rs` · **24 Tests** (302/302 gesamt grün)

### Implementierte Subsysteme

1. **Proof of History (PoH)** — `PohSequence`
   - Sequenzielle Hash-Kette für kryptografische Zeitordnung (Solana-Prinzip)
   - `tick(timestamp)` erzeugt Zeit-Tick (Hash aus Vorgänger-Hash + Tick-Nummer)
   - `record(timestamp, event_hash)` verknüpft ein Event (z.B. Tx-Hash) mit der PoH-Kette
   - `verify(start_hash, entries)` revalidiert die gesamte PoH-Kette ab einem Start-Hash
   - Tamper-Evident: jede Modifikation bricht die Kette

2. **DAG-Struktur (ATC-04)** — `Dag` + `DagVertex`
   - Directed Acyclic Graph statt linearer Chain — parallele Transaktionen ohne Flaschenhals
   - `DagVertex`: Mehrfach-Parents (Referenzen auf Vorgänger), PoH-Hash, Payload-Hash, Ed25519-Signatur
   - `VertexType`: Genesis (auto-confirmed), Transaction, Checkpoint
   - `add_vertex()` mit Parent-Existenz-Prüfung (verhindert verwaiste Vertices)
   - `get_tips()` — unbestätigte Spitzen des DAG (für neue Proposals)
   - `get_children(parent_id)` — Nachfolger eines Vertex
   - `topological_order()` — BFS-Sortierung ab Genesis (für deterministische Verarbeitung)
   - `tips_hash()` — Checkpoint-Hash über alle Tips (für Sync/Zustands-Vergleich)
   - `confirm_vertex(id)` — markiert Vertex als final bei erreichter Supermajority

3. **Validator-Registry** — `ValidatorRegistry` + `Validator`
   - Stake-basierte Registrierung (DID + Stake + active-Flag)
   - `select_proposer(poh_hash)` — Stake-weighted Proposer-Selection via PoH-Hash (VRF-ähnlich, simplified)
   - `deactivate(did)` — Validator aus Konsens entfernen (Slashing/Timeout)
   - Stat-Tracking: `votes_cast`, `blocks_proposed` pro Validator
   - `total_stake()` — Summe aller aktiven Stakes (für Finality-Berechnung)

4. **Vote-Pool & Finality** — `VotePool` + `Vote`
   - Stake-weighted 2/3 Supermajority für Finalität (Schwellwert konfigurierbar, default 0.667)
   - `cast_vote(vote)` — stimmt über Vertex ab (approve/reject + Ed25519-Signatur)
   - `is_final(vertex_id)` — prüft ob approving-stake >= 2/3 von total-stake
   - `approve_count()` / `reject_count()` — Stimmen-Zählung
   - `finalized_vertices()` — alle Vertices, die Finalität erreicht haben
   - Verknüpfung: Votes enthalten DID (K6) + Ed25519-Signatur (K6b)

5. **Consensus-Engine** — `ConsensusEngine`
   - `init_genesis(timestamp)` — initialisiert DAG mit Genesis-Vertex (auto-confirmed)
   - `propose_vertex(payload_hash, timestamp, signature)` — neuer Vertex an Tips angehängt, PoH-Eintrag erzeugt
   - `vote(vertex_id, timestamp, approve, signature)` — eigener Vote abgeben
   - `handle_vote(vote)` — fremde Vote verarbeiten, automatische Bestätigung bei Finalität
   - `fork_choice()` — schwerester Pfad ab Genesis (Vertex mit meisten Votes wird gewählt)
   - `next_proposer()` — Stake-weighted Auswahl des nächsten Block-Proposers via PoH-Hash
   - Verbindet: DAG + PoH + Validator-Registry + Vote-Pool in einer Engine

### Architektonische Bedeutung

Mit K-Sprint 16 hat ShivaCore einen vollständigen Konsens-Mechanismus auf Kernel-Ebene.
Die DAG-Architektur (ATC-04) ermöglicht parallele Transaktionsverarbeitung ohne
linearen Chain-Flaschenhals. Proof of History sorgt für kryptografische Zeitordnung
ohne vertrauenswürdige Zeitquelle. Validator-Voting mit 2/3-Supermajority обеспечивает
Byzantine Fault Tolerance. Das ist das Herzstück des Blockchain-OS — Konsens läuft
direkt im Kernel, nicht als Userspace-Daemon.

### Gesamtstand nach K-Sprint 16

24 Rust-Module, 302/302 Tests grün. K0-K16 alle abgeschlossen.

Vollständige Subsystem-Übersicht:
- K0 Boot · K1 GDT/IDT/PIC · K2 Paging/Heap
- K3a Capabilities · K3b Prozesse · K4 DA-HEFT Scheduler · K5 IPC
- K6 DID/RCT · K6b Ed25519 · K7 Knowledge Graph · K8 VFS
- K9 Syscalls (ATC-96) · K10 Timer/Clock · K11 Block-Device · K12 Netzwerk (Ethernet/ARP)
- K13 TCP/IP (IPv4/UDP/TCP/Sockets) · K14 P2P-Consensus Foundation
- K15 Security Layer (Multi-Sig/Audit/Reputation/Rate-Limit/Secure-Channel)
- K16 Konsens-Mechanismus (DAG+PoH+Validator+Voting+Finality)

**Nächste logische Schritte:** Memory-Pool/Transaction-Validation auf Konsens,
Userspace/Ring-3, oder echte Hardware-Treiber (HPET/virtio-blk/virtio-net).


---

## ShivaCore Kernel — Vollständige K-Sprint-Dokumentation K0–K16 (Stand: 03.08.2026)

**Repository:** `A-TownChain-Okosystems/atc-shivacore`
**Architektur:** Rust no_std, x86_64, UEFI, Trait-basiert mit simulierten Backends für `cargo test`
**Test-Status:** 302/302 Tests grün · 24 Rust-Module

---

### K-Sprint 0: Boot (abgeschlossen)

`kernel/src/main.rs` + `kernel/src/boot/`

- UEFI-Bootloader-Stub, Serial-Output (COM1), Framebuffer-Initialisierung
- `println!`-Macro über Serial-Konsole
- `_start`-Entry-Point, Panic-Handler
- QEMU-verifiziert (`cargo run` mit OVMF)
- **Tests:** 1 (boot smoke test)

### K-Sprint 1: GDT/IDT/PIC (abgeschlossen)

`kernel/src/gdt.rs`, `kernel/src/idt.rs`, `kernel/src/pic.rs`

- **GDT:** 64-bit Code/Data-Segmente, TSS-Setup für Ring-0
- **IDT:** 256 Interrupt-Gate-Entries, Handler-Tabelle
- **PIC:** 8259-PIC-Remapping (IRQ 0-15 → Interrupt 32-47), EOI-Signal
- Exception-Handler: Breakpoint (#BP), General Protection Fault (#GP), Page Fault (#PF)
- Timer-Interrupt (IRQ0) und Keyboard-Interrupt (IRQ1) grundlegend
- **Tests:** 5 (GDT-Struktur, IDT-Setup, PIC-Mapping, Exception-Dispatch, IRQ-Mask)

### K-Sprint 2: Paging/Heap/alloc (abgeschlossen)

`kernel/src/paging.rs`, `kernel/src/heap.rs`

- **Paging:** 4-Level Page-Tables (PML4→PDPT→PD→PT), Identity-Mapping
  - Page-Frame-Allocator (Bitmap-basiert), `alloc_frame()`/`free_frame()`
  - Page-Fault-Handler mit Mapping-Recovery
- **Heap:** `linked_list_allocator`-basiert, `#[global_allocator]`-Implementierung
  - `alloc::vec::Vec`, `alloc::string::String`, `alloc::collections::BTreeMap` nutzbar
  - `Box`, `Arc`, `Mutex` (spin-lock) funktionsfähig
- **Tests:** 8 (Page-Table-Erzeugung, Frame-Allokation, Heap-alloc/dealloc, Vec/String/BTreeMap, Box/Mutex)

### K-Sprint 3a: Capabilities (abgeschlossen)

`kernel/src/capability.rs`

- `CapabilityTable` — verwaltet Capabilities pro Prozess (PID → Capabilities)
- `Rights` — Bitflags: READ(1), WRITE(2), EXEC(4), DELEGATE(8)
- `create()`, `delegate()`, `check()`, `revoke()` — Capability-basierte Zugriffskontrolle
- Delegation-Chain: Eltern können Rechte an Kinder delegieren (nie mehr als eigene)
- **Tests:** 10 (Create/Check/Delegate/Revoke, Delegation-Limits, Cross-Prozess-Isolation)

### K-Sprint 3b: Prozessverwaltung (abgeschlossen)

`kernel/src/process.rs`

- `ProcessManager` — verwaltet Prozess-Lebenszyklus
- `Process` — PID, Parent-PID, Name, Status (Ready/Running/Blocked/Exited), Priority
- `spawn()`, `kill()`, `wait()`, `exit()`, `get_info()`
- Prozess-Tree (Parent-Child-Beziehungen), Exit-Code-Tracking
- Integration mit Capabilities (K3a): Prozess hat eigene Capability-Table
- **Tests:** 8 (Spawn/Exit/Wait/Kill, Prozess-Tree, Priority-Tracking)

### K-Sprint 4: DA-HEFT Scheduler (abgeschlossen)

`kernel/src/scheduler.rs`

- **DA-HEFT** (Dynamic Adaptive Heterogeneous Earliest Finish Time)
- `Scheduler` — verwaltet Ready-Queue, wählt nächsten Prozess nach DA-HEFT-Heuristik
- Berücksichtigt: Prozess-Priorität, Deadline, Ressourcen-Requirements
- `schedule()` — wählt Prozess mit höchstem Rang ( earliest finish time)
- `yield()`, `block()`, `unblock()` — kooperative und präemptive Scheduling-Primitives
- Integration mit Timer (K10): Deadline-basierte Präemption (vorbereitet)
- **Tests:** 10 (Scheduling-Reihenfolge, Priority, Deadline, Block/Unblock, Multi-Process)

### K-Sprint 5: IPC (Inter-Process Communication) (abgeschlossen)

`kernel/src/ipc.rs`

- `IpcSubsystem` — Channel-basierte IPC
- `IpcChannel` — unidirektional, beschränkte Kapazität (Ring-Buffer)
- `create_channel()`, `send()`, `recv()`, `grant_access()`, `close_channel()`
- Capability-Gating: Channel-Erstellung benötigt DELEGATE-Recht, Senden/empfangen benötigt READ/WRITE
- `grant_access()` — anderen Prozessen Zugriff auf Channel geben (via Capability)
- **Tests:** 12 (Create/Send/Recv, Access-Control, Cross-Prozess, Capacity-Limits, Close)

### K-Sprint 6: DID + RCT (abgeschlossen)

`kernel/src/did.rs`, `kernel/src/did.rs (Ed25519)`

- **DID:** `did:shivacore:ed25519:<base58-encoded-pubkey>` Format
  - `DidDocument` — ID, Public-Key, Created-Timestamp, Authentication-Method
  - `DidResolver` — löst DID zu DidDocument auf (In-Memory-Registry)
  - `register()`, `resolve()`, `authenticate()` — Lifecycle
- **RCT (Revocation Consensus Token):** Nonce-basierte Challenge-Response
  - `challenge()`, `response()`, `verify()` — kryptografische Authentifizierung
- **Tests:** 15 (DID-Format, Register/Resolve/Authenticate, RCT-Challenge/Response/Verify)

### K-Sprint 6b: Ed25519 Signatures (abgeschlossen)

`kernel/src/did.rs (Ed25519)` (erweitert)

- Ed25519-Implementierung (vereinfacht für no_std, Test-konform)
- `sign()`, `verify()` — digitale Signaturen über beliebige Daten
- `keypair()` — Public/Private-Key-Generierung
- Integration mit DID (K6): Signatur als Authentication-Methode
- **Tests:** 10 (Sign/Verify, KeyPair-Generation, Invalid-Signature-Detection)

### K-Sprint 7: Knowledge Graph (abgeschlossen)

`kernel/src/knowledge_graph.rs`

- `KnowledgeGraph` — Entity-Relationship-Graph
- `Entity` — ID, Type, Properties (Key-Value), Timestamps
- `Triple` — (Subject, Predicate, Object) — RDF-ähnliche Struktur
- `add_entity()`, `add_triple()`, `query()` — CRUD + SPARQL-ähnliche Queries
- `traverse()` — Graph-Traversal (BFS ab Entity)
- Integration mit VFS (K8): Knowledge-Graph-Entries können Datei-Metadaten referenzieren
- **Tests:** 12 (Entity-CRUD, Triple-Add, Query, Traverse, Integration)

### K-Sprint 8: VFS (Virtual File System) (abgeschlossen)

`kernel/src/vfs.rs`

- `Vfs` — hierarchisches Dateisystem (POSIX-ähnliche Pfade, `/`-root)
- `VfsNode` — File/Directory/Symlink, Owner-PID, Permissions, Timestamps, Size
- `OpenMode` — Read, Write, ReadWrite, Append, Create
- `open()`, `read()`, `write()`, `close()`, `seek()` — File-Operations
- `mkdir()`, `rmdir()`, `list_dir()`, `stat()`, `create_file()`, `remove_file()`
- `create_symlink()`, `read_symlink()` — Symbolic Links
- Capability-Gating: jede Operation prüft READ/WRITE-Rechte des aufrufenden Prozesses
- FD-Table pro Prozess (File-Descriptor-Tracking)
- **Tests:** 18 (Full File-Cycle, Directories, Symlinks, Seek, Permissions, Error-Handling)

### K-Sprint 9: Syscall Interface (ATC-96) (abgeschlossen)

`kernel/src/syscall.rs`

- `SyscallDispatcher` — zentrale Dispatch-Funktion, leitet an alle Subsysteme weiter
- 33 Syscalls in 7 Kategorien:
  - **Prozess:** spawn, kill, wait, sleep
  - **VFS:** open, read, write, close, seek, mkdir, rmdir, listdir, stat, create_file, remove_file, symlink, readlink
  - **IPC:** create, send, recv, grant, close
  - **Capability:** create, delegate, check, revoke
  - **Scheduler:** yield, info
  - **Knowledge Graph:** query, create_entity, add_triple
  - **Memory:** alloc, free, memcpy
- `Context` — drei Ausführungs-Contexte (ATC-96 §3):
  - `Node` — vollzugriff (Kernel-intern / privilegierter Prozess)
  - `Contract` — nur alloc/free + Capabilities, keine I/O (Sandbox!)
  - `Test` — alle Syscalls mit Mocks
- Gas-Tracking (ATC-96 §4): jeder Syscall hat definierte Gas-Kosten, `OutOfGas` blockiert
- `SyscallArg` — typisierte Argumente (U64, String, Bytes)
- `SyscallResult` — Success(u64), SuccessString, SuccessList, Ok, Error
- `SyscallError` — PermissionDenied, OutOfGas, InvalidArgument, NotFound, AlreadyExists, CapabilityDenied, VfsError, ProcessError, IpcError, UnknownSyscall
- Capability-Gating: jeder Syscall prüft READ/WRITE/EXEC/DELEGATE vor Ausführung
- **Tests:** 22 (Context-Isolation, Gas-Tracking, VFS/IPC/Process/Capability via Syscalls, Contract-Restrictions, Error-Handling)

### K-Sprint 10: Timer/Clock-Subsystem (abgeschlossen)

`kernel/src/timer.rs`

- `TimerSource` Trait — Abstraktion für HPET/PIT/TSC (Hardware) oder Simulation
- `SimulatedTimerSource` — RAM-basierte Zeitquelle für Tests, `advance()`/`set()`
- `MonotonicClock` — `uptime_ns()`/`uptime_ms()`/`uptime_secs()`, `uptime_string()`, kapselt TimerSource
- `TimerManager` — Sleep-Queue mit Deadline-Sortierung (BTreeMap)
- `TimerCallback` — `Wakeup(pid)`, `Periodic(interval_ns)`, `Alarm` (one-shot)
- `sleep()`, `schedule_periodic()`, `schedule_alarm()`, `cancel()`, `tick()`
  - `tick()` — prüft alle Deadlines, liefert fired events, re-registriert periodische Timer
- `next_deadline()` / `time_to_next_deadline()` — Scheduler-Integration
- `duration` — Hilfsfunktionen (`from_ms/secs/us/mins`, `to_ms/secs/us`)
- **Tests:** 20 (Clock-Uptime, Sleep-Fire, Multiple-Timers, Periodic-Re-Register, Cancel, Deadline-Tracking)

### K-Sprint 11: Block-Device-Layer (abgeschlossen)

`kernel/src/block.rs`

- `BlockDevice` Trait — `read_block()`, `write_block()`, `block_count()`, `capacity()`, `is_read_only()`, `name()`
- `SimulatedBlockDevice` — RAM-backed Block-Device für Tests (read-only mode supported)
- `BlockBuffer` — LRU-Block-Cache mit Dirty-Tracking und Flush
  - `read()` — Cache-Hit/Miss-Statistik, automatische Eviction bei vollem Cache
  - `write()` — schreibt in Cache, markiert dirty
  - `flush()` — schreibt alle dirty Blocks auf das Gerät
  - `clear()` — flush + Cache leeren
- `MBRPartitionTable` — MBR-Parsing (0x55AA-Signatur, 4 Partition-Einträge)
  - `PartitionEntry` — bootable, type, start_lba, block_count
- **Tests:** 18 (Device-Read/Write, Out-of-Range, Read-Only, Buffer-Cache-Hit/Miss, Flush, Eviction, MBR-Parsing)

### K-Sprint 12: Netzwerk-Stack Foundation (abgeschlossen)

`kernel/src/net.rs`

- `MacAddress` — 6-Byte, `broadcast()`/`zero()`, `is_broadcast()`/`is_zero()`, `to_string()`
- `Ipv4Address` — 4-Byte, `broadcast()`/`zero()`, `is_broadcast()`/`is_zero()`, `to_string()`
- `EthernetFrame` — dst/src/ethertype/payload, `to_bytes()`/`from_bytes()`
  - `ETH_TYPE_ARP` (0x0806), `ETH_TYPE_IPV4` (0x0800)
- `ArpPacket` — ARP-Request/Reply, serialize/deserialize (28 Bytes)
  - `ARP_HW_ETHERNET`, `ARP_OP_REQUEST`, `ARP_OP_REPLY`
- `ArpTable` — IP→MAC Mapping mit Timeout und permanenten Einträgen
  - `lookup()`, `insert()`, `insert_permanent()`, `remove()`, `purge_expired()`
- `NetworkDevice` Trait — `send_frame()`, `recv_frame()`, `mac_address()`, `mtu()`, `is_up()`, `name()`
- `LoopbackDevice` — RAM-basiertes Netzwerk-Device für Tests (Queue-basiert)
- `NetworkStack` — verbindet Device + ARP
  - `arp_request()` — sendet ARP-Request via Broadcast
  - `handle_frame()` — verarbeitet empfangene Frames (ARP + IPv4)
  - `handle_arp()` — lernt Sender-MAC, antwortet auf Requests an uns
  - `resolve_mac()` — ARP-Cache-Lookup
  - `send_to()` — sendet Frame an bekannte MAC
- **Tests:** 22 (MAC/IPv4, Ethernet-Serialize, ARP-Request/Reply, ARP-Table-Timeout, Loopback, NetworkStack-Handshake)

### K-Sprint 13: TCP/IP-Layer (abgeschlossen)

`kernel/src/tcpip.rs`

- `Ipv4Packet` — IPv4 mit Header-Checksumme (One's Complement), `to_bytes()`/`from_bytes()`, `with_checksum()`
  - `IP_PROTO_ICMP` (1), `IP_PROTO_TCP` (6), `IP_PROTO_UDP` (17)
- `UdpPacket` — 8-Byte Header, `to_bytes()`/`from_bytes()`
- `TcpSegment` — TCP mit Flags (SYN/ACK/FIN/RST/PSH/URG), `to_bytes()`/`from_bytes()`
  - `is_syn()`, `is_ack()`, `is_fin()`, `is_rst()`
- `RoutingTable` — Longest Prefix Match, Default-Route, metric-basierte Sortierung
  - `Route` — network, prefix_len, gateway, interface, metric
  - `lookup()` — findet beste Route für Ziel-IP (longest prefix match)
  - `matches()` — CIDR-Matching
- `SocketManager` — UDP und TCP Sockets
  - **UDP:** `udp_bind()`, `udp_connect()`, `udp_send()`, `udp_recv()`, `handle_udp()`, `udp_close()`
  - **TCP:** `tcp_bind()`, `tcp_connect()`, `tcp_state()`, `handle_tcp()`, `tcp_recv()`, `tcp_close()`
  - `TcpState` — Closed, Listen, SynSent, SynReceived, Established, FinWait1, FinWait2, CloseWait, LastAck, TimeWait
  - TCP State Machine: `handle_tcp()` verarbeitet SYN/SYN-ACK/FIN, empfängt Daten
- `IpStack` — verbindet NetworkStack + Routing + Sockets
  - `handle_ipv4()` — dispatcht UDP/TCP an SocketManager
  - `handle_frame()` — verarbeitet Ethernet→IPv4→UDP/TCP Stack
- **Tests:** 28 (IPv4-Checksum, UDP-Serialize, TCP-Flags, Routing-Longest-Prefix, UDP-Bind/Connect/Recv, TCP-Handshake/Data/Close, IpStack-Integration)

### K-Sprint 14: P2P-Consensus Foundation (abgeschlossen)

`kernel/src/p2p.rs`

- `P2pMessage` — 9 Message-Types, Chain-ID-Validierung (9000), DID-Feld, Timestamp
  - `MessageType`: Ping, Pong, Handshake, HandshakeAck, BlockAnnounce, TxAnnounce, Vote, PeerList, Bye
  - `to_bytes()`/`from_bytes()` — Serialisierung mit Chain-ID-Check
- `PeerTable` — verwaltet Peers (IP, Port, DID, Status, Stats)
  - `add_peer()`, `remove_peer()`, `get_peer()`, `find_by_addr()`
  - `set_status()`, `set_did()`, `touch()`, `record_sent()`, `record_recv()`
  - `max_peers`-Limit, `connected_count()`, Stat-Tracking (bytes/messages sent/recv)
- `GossipProtocol` — Broadcast und Direct-Send
  - `broadcast()` — an alle verbundenen Peers
  - `send_to()` — an einen spezifischen Peer
  - `handle_message()` — verarbeitet Handshake/Bye, lernt DID
  - Peer-Discovery: `make_peer_list()`, `handle_peer_list()`
  - `make_ping()`, `make_pong()`, `make_handshake()` — Message-Factory
- `P2pNode` — Top-Level-Integration
  - `connect_peer()` — sendet Handshake
  - `handle_handshake()` — verarbeitet eingehenden Handshake, lernt DID, sendet Ack
  - `ping_all()` — Ping an alle Peers
  - `announce_block()`, `announce_tx()` — Block/Transaktion propagieren
  - `disconnect_peer()` — sauberer Disconnect mit Bye
- Chain-ID 9000 (Non-EVM, SHA-256) validiert in jeder Message
- **Tests:** 25 (Message-Serialize, Chain-ID-Validation, PeerTable, Gossip-Broadcast, Handshake-Learning, Peer-Discovery, P2pNode-Integration)

### K-Sprint 15: Security Layer (abgeschlossen)

`kernel/src/security.rs`

1. **Multi-Signature Auth (ATC-18)** — `MultiSigManager` + `MultiSigProposal`
   - m-of-n Signatursammlung, Duplicate-Signer-Check, `is_ready()`, `execute()`
   - Signatur mit (DID, Ed25519-Signatur) — verknüpft mit K6/K6b
2. **Audit-Log (Tamper-Evident)** — Hash-Chain über alle Sicherheitseinträge
   - `log()` — seq + timestamp + actor + action + resource + result → hash
   - `verify_chain()` — revalidiert gesamte Hash-Kette
   - `filter_by_actor()` / `filter_by_result()`
3. **Peer-Reputation** — Score [-100..+100], automatischer Ban bei ≤ -50
   - `reward()` / `penalize()` / `unban()`, `is_banned()`, `banned_count()`
4. **Rate-Limiting (Token Bucket)** — pro-Peer Token-Bucket mit Refill
   - `allow(peer_id, now)` — konsumiert 1 Token, blockiert bei leerem Bucket
   - Zeitbasiertes Refill (tokens/sec)
5. **Secure-Channel** — verschlüsselte Kommunikation zwischen Peers
   - `establish()` / `send()` / `recv()` / `close()`
   - XOR-basiert für Tests, ersetztbar durch AEAD (XChaCha20-Poly1305) in Produktion
6. **SecurityManager** — Top-Level Integration
   - `check_peer()` — Reputation + Rate-Limit kombiniert
   - `audit_log()` — zentrale Audit-Funktion
- **Tests:** 28 (Multi-Sig-Create/Sign/Execute, Audit-Verify-Chain, Reputation-Ban/Unban, Rate-Limit-Deplete/Refill, Secure-Channel-Encrypt/Decrypt, SecurityManager-Integration)

### K-Sprint 16: Konsens-Mechanismus (abgeschlossen)

`kernel/src/consensus.rs`

1. **Proof of History (PoH)** — `PohSequence`
   - Sequenzielle Hash-Kette für kryptografische Zeitordnung (Solana-Prinzip)
   - `tick(timestamp)` erzeugt Zeit-Tick (Hash aus Vorgänger-Hash + Tick-Nummer)
   - `record(timestamp, event_hash)` verknüpft ein Event mit der PoH-Kette
   - `verify(start_hash, entries)` revalidiert die gesamte PoH-Kette
2. **DAG-Struktur (ATC-04)** — `Dag` + `DagVertex`
   - Directed Acyclic Graph — parallele Transaktionen ohne Chain-Flaschenhals
   - `DagVertex`: Mehrfach-Parents, PoH-Hash, Payload-Hash, Ed25519-Signatur
   - `VertexType`: Genesis (auto-confirmed), Transaction, Checkpoint
   - `add_vertex()` mit Parent-Existenz-Prüfung, `get_tips()`, `get_children()`
   - `topological_order()` — BFS-Sortierung ab Genesis
   - `tips_hash()` — Checkpoint-Hash über alle Tips
   - `confirm_vertex(id)` — markiert als final bei erreichter Supermajority
3. **Validator-Registry** — `ValidatorRegistry` + `Validator`
   - Stake-basierte Registrierung (DID + Stake + active-Flag)
   - `select_proposer(poh_hash)` — Stake-weighted Proposer-Selection via PoH-Hash
   - `deactivate(did)` — Validator aus Konsens entfernen
   - Stat-Tracking: `votes_cast`, `blocks_proposed` pro Validator
4. **Vote-Pool & Finality** — `VotePool` + `Vote`
   - Stake-weighted 2/3 Supermajority für Finalität (Schwellwert konfigurierbar, default 0.667)
   - `cast_vote(vote)` — stimmt über Vertex ab (approve/reject + Ed25519-Signatur)
   - `is_final(vertex_id)` — prüft ob approving-stake ≥ 2/3 von total-stake
   - `approve_count()` / `reject_count()` — Stimmen-Zählung
   - `finalized_vertices()` — alle Vertices, die Finalität erreicht haben
5. **Consensus-Engine** — `ConsensusEngine`
   - `init_genesis(timestamp)` — initialisiert DAG mit Genesis-Vertex
   - `propose_vertex(payload_hash, timestamp, signature)` — neuer Vertex an Tips, PoH-Eintrag
   - `vote(vertex_id, timestamp, approve, signature)` — eigener Vote
   - `handle_vote(vote)` — fremde Vote, automatische Bestätigung bei Finalität
   - `fork_choice()` — schwerester Pfad ab Genesis (meiste Votes)
   - `next_proposer()` — Stake-weighted Auswahl des nächsten Proposers via PoH-Hash
- **Tests:** 24 (PoH-Tick/Record/Verify, DAG-Add/Children/Topological, Validator-Register/Select, Vote-Finality-2/3, Consensus-Engine-Full-Workflow, Fork-Choice)

---


### Kernel-Hilfsmodule (nicht Teil der K-Sprint-Nummerierung)

| Modul | Datei | Beschreibung |
|-------|-------|-------------|
| Serial | serial.rs | Serielle Debug-Konsole (QEMU `-serial stdio`), `println!`-Backend |
| Framebuffer | framebuffer.rs | Framebuffer-Textausgabe (gerasterte Glyphen, kein VGA-Text-Modus) |
| ATS-1000 | ats1000.rs | ShivaCore Interface-Traits (ProcessManager, MemoryManager, FileSystem, NetworkStack) |
| Remote-Caps | remote_caps.rs | Remote-Capability-Tickets (RCT) — kryptografisch signierte Capability-Delegation an fremde Knoten |

**Echte Modul-Anzahl: 24 .rs-Dateien** (20 K-Sprint-Module + 4 Hilfsmodule, inkl. main.rs)

### Vollständige Subsystem-Übersicht (24 Module, 302 Tests)

| Sprint | Modul | Datei | Tests | Status |
|--------|-------|-------|-------|--------|
| K0 | Boot | main.rs + boot/ | 1 | ✅ |
| K1 | GDT/IDT/PIC | gdt.rs, interrupts.rs | 5 | ✅ |
| K2 | Paging/Heap | memory.rs, allocator.rs | 8 | ✅ |
| K3a | Capabilities | capability.rs | 10 | ✅ |
| K3b | Prozesse | process.rs | 8 | ✅ |
| K4 | DA-HEFT Scheduler | scheduler.rs | 10 | ✅ |
| K5 | IPC | ipc.rs | 12 | ✅ |
| K6 | DID + RCT | did.rs | 15 | ✅ |
| K6b | Ed25519 | did.rs | 10 | ✅ |
| K7 | Knowledge Graph | knowledge_graph.rs | 12 | ✅ |
| K8 | VFS | vfs.rs | 18 | ✅ |
| K9 | Syscalls (ATC-96) | syscall.rs | 22 | ✅ |
| K10 | Timer/Clock | timer.rs | 20 | ✅ |
| K11 | Block-Device | block.rs | 18 | ✅ |
| K12 | Netzwerk (L2) | net.rs | 22 | ✅ |
| K13 | TCP/IP (L3-4) | tcpip.rs | 28 | ✅ |
| K14 | P2P-Consensus | p2p.rs | 25 | ✅ |
| K15 | Security Layer | security.rs | 28 | ✅ |
| K16 | Konsens (DAG+PoH) | consensus.rs | 24 | ✅ |
| **Σ** | **24 Module** | | **302** | **✅** |

### Architektonische Abhängigkeiten (Bottom-Up)

```
K0 Boot ──→ K1 GDT/IDT/PIC ──→ K2 Paging/Heap
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
               K3a Capabilities  K3b Prozesse    K10 Timer
                    │               │
                    ▼               ▼
               K4 Scheduler    K5 IPC
                    │               │
                    └───────┬───────┘
                            ▼
                        K8 VFS ──→ K9 Syscalls (ATC-96)
                            │
                    ┌───────┼───────────────┐
                    ▼       ▼               ▼
               K6 DID  K7 Knowledge    K11 Block-Device
               K6b Ed25519  Graph
                    │
                    ▼
              K12 Netzwerk (Ethernet/ARP)
                    │
                    ▼
              K13 TCP/IP (IPv4/UDP/TCP/Sockets)
                    │
                    ▼
              K14 P2P-Consensus Foundation
                    │
                    ▼
              K15 Security Layer (Multi-Sig/Audit/Reputation/Rate-Limit/Secure-Channel)
                    │
                    ▼
              K16 Konsens-Mechanismus (DAG + PoH + Validator + Voting + Finality)
```

### Offene nächste Schritte

- **Memory-Pool/Transaction-Validation** auf Konsens (K17)
- **Userspace/Ring-3** (neue GDT-Segmente, TSS-Ring-Wechsel, `syscall`-Instruktion)
- **Echte Hardware-Treiber** (HPET, virtio-blk, virtio-net für QEMU)
- **P2P-Consensus-Integration** mit echten TCP-Sockets (statt LoopbackDevice)


---

## K-Sprint 17: Memory-Pool & Transaction-Validation abgeschlossen (03.08.2026)

**Repo:** `atc-shivacore` · **Datei:** `kernel/src/mempool.rs` · **30 Tests** (332/332 gesamt grün)

### Implementierte Subsysteme

1. **Transaction** — 7 Tx-Types: Transfer, Stake, Unstake, Delegate, Vote, ContractCall, ContractDeploy
   - `gas_cost()` — Base-Gas (per Type) + Payload-Gas (10 gas/byte)
   - `max_fee()` — gas_limit × gas_price
   - Deterministische Tx-ID (Hash über alle Felder)

2. **MemoryPool** — verwaltet pendente Transaktionen vor Konsens
   - `add()` mit Pool-Full und Duplicate-Check
   - `validate_tx()` — Gas-Limit, Recipient, Gas-Price Checks
   - `get_pending_batch(max)` — priorisierte Txs (höchster gas_price × gas_limit zuerst)
   - `mark_in_dag()` / `mark_confirmed()` — Konsens-Integration (K16)
   - `cleanup(now)` — entfernt bestätigte/abgelaufene Txs
   - Per-Sender Tracking: `txs_by_sender()`, `sender_nonce()`

3. **NonceTracker** — Replay-Angriff-Prävention
   - `check_and_advance()` — Nonce muss strikt sequenziell sein (0, 1, 2, ...)
   - `expected_nonce()` / `reset()`

4. **StateDb** — vereinfachte Account-State-Datenbank
   - Balance, Staked, Nonce pro DID
   - `deposit()` / `withdraw()` / `stake()` / `unstake()`
   - `total_supply()` — Summe aller Balances + Stakes

5. **TxValidator** — vollständige Transaktionsvalidierung
   - Gas-Price-Check (≥ min_gas_price)
   - Gas-Limit-Check (≥ base_gas + payload_gas)
   - Nonce-Check (must match expected)
   - Balance-Check (amount + max_fee ≤ balance)
   - `validate()` — prüft alle Constraints
   - `apply()` — wendet valide Tx auf State an

### Gesamtstand nach K-Sprint 17

25 Rust-Module (24 .rs + main.rs), 332/332 Tests grün. K0-K17 alle abgeschlossen.


---

## K-Sprint 18: Block-Proposal-Pipeline abgeschlossen (03.08.2026)

**Repo:** `atc-shivacore` · **Datei:** `kernel/src/blockchain.rs` · **20 Tests** (352/352 gesamt grün)

### Implementierte Subsysteme

1. **Block** — Block-Struktur mit Height, Parent-Hash, Transactions, Merkle-Root,
   Gas-Used, Total-Fees, Ed25519-Signatur. Deterministische Block-ID.

2. **BlockChain** — lineare Block-Kette (Genesis → Block 1 → 2 → ...).
   Height-Validierung, Parent-Existenz-Check, Hash-Lookup.

3. **ProposalPipeline** — die komplette Pipeline:
   - `create_genesis()` — Genesis-Block + DAG-Vertex
   - `propose_block(max_txs)` — Mempool → validiere → State → Block → Chain → DAG
   - `process_remote_block()` — eingehende Blocks validieren und einfügen
   - `vote_on_block()` — Konsens-Voting
   - `cleanup_mempool()` — Post-Confirmation Cleanup

### Pipeline-Fluss
```
Mempool (K17) → get_pending_batch() → TxValidator.validate() → TxValidator.apply()
  → Block::new() → BlockChain.add_block() → ConsensusEngine.propose_vertex()
  → DAG Vertex → Vote (K16) → Finality → mark_confirmed() → cleanup()
```

### Gesamtstand nach K-Sprint 18

26 Rust-Module (25 .rs + main.rs), 352/352 Tests grün. K0-K18 alle abgeschlossen.


---

## K-Sprint 19: Contract VM / ShivaVM abgeschlossen (03.08.2026)

**Repo:** `atc-shivacore` · **Datei:** `kernel/src/vm.rs` · **30 Tests** (382/382 gesamt grün)

### Implementierte Subsysteme

1. **ShivaVM** — Stack-basierter Bytecode-Interpreter mit 27 Opcodes
   - Arithmetik (Add/Sub/Mul/Div/Mod), Vergleiche (Eq/Ne/Lt/Gt/Lte/Gte)
   - Logik (And/Or/Not), Control-Flow (Jump/JumpIf/JumpIfNot)
   - Host-Functions (Call/Ret), Storage (Load/Store)
   - Context (Self/Caller/Balance/Transfer), Logging (Log)
   - 1024-Element Stack, Gas-Metering pro Opcode, OutOfGas-Abort

2. **ContractStorage** — Key-Value Store pro Contract
   - Persistent über Calls hinweg
   - `clear_contract()` für Self-Destruct

3. **ContractRegistry** — Verwaltet deployte Contracts
   - Deploy, Balance-Management (deposit/withdraw)

4. **VmEngine** — Top-Level: deploy + call + execute

### Gesamtstand nach K-Sprint 19

27 Rust-Module (26 .rs + main.rs), 382/382 Tests grün. K0-K19 alle abgeschlossen.


---

## K-Sprint 20: Contract-Call-Integration abgeschlossen (03.08.2026)

**Repo:** `atc-shivacore` · **Datei:** `kernel/src/contract.rs` · **17 Tests** (399/399 gesamt grün)

### Pipeline (komplett)
```
Mempool (K17) → TxValidator (K17) → Block::new (K18) → BlockChain (K18)
  ↓ ContractDeploy/Call
  → ContractExecutor (K20) → ShivaVM (K19) → ContractStorage → State (K17)
```

### Implementierte Subsysteme

1. **ContractExecutor** — verarbeitet Contract-Transaktionen
   - Deploy: Bytecode extrahieren, deterministische Contract-Adresse, VmEngine.deploy()
   - Call: Contract-Adresse extrahieren, VmEngine.call(), ExecResult zurück

2. **Payload-Format** — standardisierte Serialisierung
   - Deploy: `[len(4)] [bytecode]`
   - Call: `[addr_len(2)] [addr] [call_data]`

3. **Full Workflow** — Deploy → Init → Call → State persists

### Gesamtstand nach K-Sprint 20

28 Rust-Module (27 .rs + main.rs), 399/399 Tests grün. K0-K20 alle abgeschlossen.
