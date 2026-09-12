# KAI-OS Core Runtime — Node

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
└── network/            # kai-os-network: P2P Transport + Discovery + Peer Security (S07-S09)
    ├── peer.rs         # PeerId (Ed25519-Pubkey), PeerStore (Dedup, Stale-Eviction)
    ├── discovery.rs    # ANNOUNCE / PING-PONG / PEER_LIST
    ├── auth.rs         # Challenge-Response-Handshake + Nonce-Registry (Replay-Schutz)
    ├── session.rs      # SecureSession: Seq-Nummern + signierte Envelopes
    └── transport.rs    # Length-Prefix-Framing (fail-closed)
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

## Subsysteme (S01: Stubs)

`consensus` · `p2p` · `state-sync` · `ai-runtime` · `storage` · `security`
Echte Implementierungen entstehen in S04–S12 (Sandbox, P2P Transport, State Sync).
Der Supervisor implementiert Consensus-**Infrastruktur** (Orchestrierung),
niemals Consensus-**Semantik** (AD-008.4).

## Determinismus

Kein RNG, keine Wall-Clock-Timestamps im Audit-Hash (REQ-ENG-002).
Restart-Backoffs sind fixe Konfigurationswerte. Tests laufen ohne Netz- und Zeitabhängigkeit.
