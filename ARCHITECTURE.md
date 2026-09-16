---
document_id: ATC-DOC-ARC-001
title: Repository Architecture Specification
version: 1.1.0
status: active
owner: A-TownChain-Okosystems
created: 2026-09-07
updated: 2026-09-16
standard: ATC-STD-MD-001
---

# Architecture Specification — a-townchain-os

## Übersicht

`a-townchain-os` bildet die Integrationsschicht Layer L7 (Domain Integration) des A-TownChain-Ökosystems. Die native KAI-OS-Implementierung liegt im Rust-Workspace `kai-os/` und wird durch CI/CD, Governance und Windows-Release- tooling integriert.

## Workspace

Der kanonische Rust-Workspace ist:

```text
kai-os/Cargo.toml
```

Der Workspace verwendet Cargo resolver 2 und umfasst aktuell 11 Mitglieder:

```text
node
runtime
network
state
syncd
ai
keyring
health
cli
pkg
integration
```

Es gibt keinen Root-`Cargo.toml`. Root-Dokumentation und Befehle dürfen daher keinen Root-Cargo-Workspace voraussetzen.

## Komponenten

- **KAI-OS Rust Workspace:** native Runtime-, Node-, Netzwerk-, State-, Sync-, AI-, Keyring-, Health-, CLI-, Package- und Integration-Komponenten.
- **CI/CD:** Governance-, Dependency-Review-, Integration- und Release-Workflows.
- **Release Stack:** Windows x64 Build, Signierung, Signaturprüfung, SBOM, SHA-256-Checksummen und Build-Provenance.
- **Packaging:** Windows/Inno-Setup-Artefakte und zugehörige SignPath-Signierung.
- **Documentation/Evidence:** Status-, Audit-, Architektur- und Governance-Dokumentation.

Die frühere Beschreibung eines Root-Cargo-Workspaces mit `scripts/sync_modules.py` entspricht nicht dem aktuellen Repository-Baum und ist entfernt.

## Data Flow & Integration

```text
Canonical product repositories
        │
        ▼
A-TownChain ecosystem interfaces
        │
        ▼
a-townchain-os / kai-os workspace
        │
        ├── node / runtime
        ├── network / syncd
        ├── state
        ├── ai / keyring / health
        ├── cli / pkg
        └── integration
        │
        ▼
CI validation → signed release artifacts
```

The integration repository must not become a duplicate source of truth for canonical blockchain consensus, ATCLang semantics or the ShivaCore kernel.

## KAI-OS — Architekturbegriff (ATC-ARCH-001)

> **KAI-OS = Cryptographic AI Operating System Architecture** — der übergeordnete
> Architekturbegriff für den kryptografisch abgesicherten AI-OS-Stack.
> KAI-OS ist KEIN separates Betriebssystem-Repository neben dem eigentlichen OS.
>
> Die sechs Kernkomponenten: ATCLang (Sprache) · ShivaCore (Kernel) · ATC-VM
> (Execution) · A-TownChain (Trust/Consensus) · Aurora OS (AI) · GlobusOS
> (Betriebssystem). Dieses Repo stellt die Integrations-/Orchestrierungsschicht (L7)
> und die KAI-OS-Workspace-Implementierung bereit.

## Boundary Rules

- ATCLang remains canonical for on-chain semantics.
- ATC-VM is the deterministic execution boundary.
- Rust carries native chain/runtime/system infrastructure.
- ShivaCore kernel responsibilities remain with the canonical kernel source and are not silently duplicated here.
- GlobusOS remains the operating-system platform layer.
- `a-townchain-os` coordinates integration; it does not redefine canonical component ownership.

Standard: `ATC-ARCH-001` in the organization standards registry.
