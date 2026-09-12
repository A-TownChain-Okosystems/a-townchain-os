# KAI-OS Core Runtime — Node

> **Terminologie (ATC-ARCH-001):** KAI-OS ist der Architekturbegriff für den
> Gesamtstack — kein Betriebssystem. Dieses Verzeichnis enthält die Core-Runtime-
> Implementierung der KAI-OS-Architektur im Integrations-Repo (a-townchain-os, L7).
> Das eigentliche Betriebssystem ist GlobusOS.

> Implementierungsblock S01–S03 · [Issue #102](https://github.com/A-TownChain-Okosystems/a-townchain-os/issues/102)
> Spezifikation: [KAI-CORE-RUNTIME-001](../docs/architecture/KAI-CORE-RUNTIME-001.md) · Sprachgrenze: [AD-008](../docs/architecture/AD-008.md) (native Runtime = Rust)

## Struktur

```
kai-os/
├── node/               # kai-os-node Daemon (Orchestrierungsebene, S01-S03)
├── runtime/            # kai-os-runtime: Sandbox + Resources + Scheduler (S04-S06)
    ├── capability.rs   # Capability Policy — deny by default
    ├── resources.rs    # Resource Manager — Quota-Enforcement pro Sandbox
    ├── sandbox.rs      # Policy -> Resource -> Execution (fail-closed)
    └── scheduler.rs    # Deterministischer Round-Robin
├── network/            # kai-os-network: P2P Transport + Discovery + Peer Security (S07-S09)
    ├── peer.rs         # PeerId (Ed25519-Pubkey), PeerStore (Dedup, Stale-Eviction)
    ├── discovery.rs    # ANNOUNCE / PING-PONG / PEER_LIST
    ├── auth.rs         # Challenge-Response-Handshake + Nonce-Registry (Replay-Schutz)
    ├── session.rs      # SecureSession: Seq-Nummern + signierte Envelopes
    └── transport.rs    # Length-Prefix-Framing (fail-closed)
├── state/              # kai-os-state: Sync + Snapshots + Merkle Verification (S10-S12)
    ├── merkle.rs       # Merkle-Tree (sortierte Entries), Inclusion-Proofs
    ├── state.rs        # StateStore (BTreeMap), Tx-Modell (Set/Remove)
    ├── snapshot.rs     # Snapshot mit Height/Tip/Root, Verifikation gegen vertrauten Root
    └── sync.rs         # SyncEngine: strikte Höhen, Prev-Kette, Root-Verifikation, Atomicität
├── ai/                 # kai-os-ai: AI Runtime + IPC + Audit Trail (S13-S15)
    ├── ipc.rs          # IPC-Gateway: Identity/Capability/Schema/Replay/Audit — kein MQ
    ├── proposal.rs     # Proposal-Registry: Proposed → Specified → HandedToVM (keine Ausführung)
    └── audit.rs        # Audit-Pipeline mit SHA-256-Hash-Chain + Queries
└── keyring/            # kai-os-keyring: Ed25519-Key-Isolation (S16-S18)
    └── keyring.rs      # Keys verlassen die Boundary NIE: nur Public + Signaturen, Revoke/Rotation
    ├── src/
    │   ├── main.rs     # Boot-Sequenz, Signal-Handling, Tick-Loop
    │   ├── lifecycle.rs    # State-Machine: INIT→BOOT→RUNNING→DEGRADED→SHUTDOWN→STOPPED
    │   ├── supervisor.rs   # Subsystem-Überwachung, Crash-Restart-Policy, State-Persistenz
    │   ├── health.rs       # Worst-of Health-Aggregation
    │   ├── config.rs      # Fail-Closed-Validierung (kein Boot bei ungültiger Config)
    │   ├── shutdown.rs     # Graceful Drain (umgekehrte Start-Reihenfolge, Report)
    │   └── audit.rs        # Append-only Audit-Log mit SHA-256-Hash-Chain
    └── tests/
        └── node_integration.rs  # 14 Tests — alle Akzeptanzkriterien aus Issue #102
```

## Boot-Sequenz (fail-closed)

```
Config validieren (Exit 2 bei Fehler)
  → Root-Guard: euid=0 verweigert Boot (außer allow_root=true)
  → Audit-Logger initialisieren (Hash-Chain)
  → Lifecycle: INIT → BOOT
  → Supervisor.start_all (fail-closed: Abbruch + Rollback bei Start-Fehler)
  → Lifecycle: BOOT → RUNNING
  → Signal-Handler: SIGTERM/SIGINT → geordnetes Herunterfahren
  → Tick-Loop: Subsystem-Health → DEGRADED ↔ RUNNING
  → Shutdown: Drain in umgekehrter Start-Reihenfolge → STOPPED (Exit 0)
```

## Ausführen

```bash
cd kai-os
cargo test                          # 14 Integrationstests
cargo run -- /pfad/zur/config.json  # Daemon starten
kill -TERM <pid>                    # Graceful Shutdown (Exit 0)
```

## Runtime (S04–S06, Issue #103)

Ausführungskette **Policy → Sandbox → Capability → Execution**:
- Capability-Builder: CPU/Memory/Storage-Quotas, Port-basierte Network-Policy (inbound/outbound getrennt), Syscall-Allowlist, Crypto-Capability — alles **deny by default**
- Resource-Manager: Verbrauchs-Tracking, exakt-am-Limit ok, Überschreitung → Fehler; Memory mit alloc/free (kein Negativsaldo), Storage append-only
- Sandbox: Operationen nur nach Policy-Gate + Ressourcen-Buchung; Isolationstest: erschöpft Sandbox A ihr Budget, arbeitet B unbeeinflusst weiter
- Scheduler: Round-Robin, identische Registration → identische Turn-Sequenz (deterministisch, REQ-ENG-002)

## Network (S07–S09, Issue #104)

Kette: `Peer Discovery → Secure Transport → Peer Authentication`
- PeerId deterministisch aus Ed25519-Pubkey (Keypairs aus Seeds, kein RNG — REQ-ENG-002)
- Challenge-Response-Handshake, Nonces strikt monoton (Replay → Fehler), Session-ID via SHA-256
- SecureSession: Sequenznummern strikt steigend, signierte Envelopes — Payload-Manipulation bricht die Verifikation
- Length-Prefix-Framing: trunzierte/übergroße Frames fail-closed abgewiesen
- Discovery: Announce-Dedup (Upsert über PeerId), Ping→Pong, PeerList-Merge, deterministisch sortierte Peer-Listen, Stale-Eviction

## State (S10–S12, Issue #105)

Kernprinzip: **Ein Snapshot wird NIEMALS vertraut, sondern gegen einen kryptographisch definierten State-Root verifiziert.**
- Merkle-Root deterministisch (Einfüge-Order egal), Inclusion-Proofs mit Manipulations-Detection
- SyncEngine akzeptiert einen Block NUR bei: Höhe = Tip+1 (keine Lücken), Prev-Hash = Tip-Hash (Kontinuität), recomputeter Root == claimed Root (Verifikation statt Vertrauen)
- Atomic: ungültige Blöcke verändern den State nicht (Scratch-Apply → Verifikation → Commit)
- Fork-Detection vor Höhen-Check; Duplikate abgewiesen; deterministisches Replay-Test (gleiche Blöcke → identischer Root)

## AI Runtime (S13–S15, Issue #106)

Kernregel (AD-008 §7): **AI may propose. ATCLang specifies. ATVM executes. ATC commits.**
- IPC-Gateway: Reihenfolge verbindlich Identity → Capability → Replay → Schema → Audit; deny by default; kein Message-Queue, sondern eine standardisierte Schnittstelle
- Proposal-Registry: KI-Vorschläge sind **Daten, keine Ausführungen** — deterministische IDs (Idempotenz), strikter Lifecycle Proposed → Specified → HandedToVM, danach terminal (Verantwortung bei ATVM/Consensus-Stack)
- Architektur-Invariante: die Crate besitzt **keine API, die Chain-State mutiert**
- Audit-Pipeline: jede Zustellung UND jede Abweisung erzeugt einen Event; Hash-Chain verifizierbar

## Keyring (S16–S18, Issue #107)

Kernregel: **Keys verlassen die Keyring-Boundary NIE.**
- Keine API gibt privates Schlüsselmaterial heraus — nur Public Keys (32 B) und Signaturen (64 B)
- Import ausschließlich über Seed-Bytes (deterministisch, kein RNG — REQ-ENG-002)
- Revoke: Key raus, Secret wird beim Drop gelöscht (ed25519-dalek Zeroize-on-Drop); danach fail-closed
- Rotation: neues Secret, neuer Public Key — alte Signaturen bleiben mit dem extern aufbewahrten alten Public Key prüfbar
- Kompatibilitätstest: identischer Seed → identischer Public Key wie kai-os-network (eine Quelle der Wahrheit)

## Subsysteme (S01: Stubs)

`consensus` · `p2p` · `state-sync` · `ai-runtime` · `storage` · `security`
Echte Implementierungen entstehen in S04–S12 (Sandbox, P2P Transport, State Sync).
Der Supervisor implementiert Consensus-**Infrastruktur** (Orchestrierung),
niemals Consensus-**Semantik** (AD-008.4).

## Determinismus

Kein RNG, keine Wall-Clock-Timestamps im Audit-Hash (REQ-ENG-002).
Restart-Backoffs sind fixe Konfigurationswerte. Tests laufen ohne Netz- und Zeitabhängigkeit.
