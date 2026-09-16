# ATC A-TownChain OS

> Integration monorepo for assembling and validating the A-TownChain ecosystem.

[![ATC COMPLIANCE](https://img.shields.io/badge/ATC%20COMPLIANCE-AUDIT%20IN%20PROGRESS-yellow)](docs/audits/REPOSITORY-AUDIT-2026-09-16.md)

**Project:** `a-townchain-os`  
**Organization:** `A-TownChain-Okosystems`  
**Status:** `development`  
**Version:** `0.1.0`  
**License:** `Apache-2.0`  
**Standard:** `ATC-STD-README-001`

## Purpose

`a-townchain-os` is the central integration and orchestration repository. It brings together ecosystem integration code, the KAI-OS Rust workspace, release tooling, CI/CD and governance validation.

It is an **integration layer**, not a replacement for the individual canonical repositories.

## Scope

This repository covers integration concerns such as:

- the Rust workspace under `kai-os/`;
- KAI-OS node/runtime/state/network integration;
- CI/CD and governance workflows;
- Windows packaging and release verification;
- cross-component validation and system-level tests;
- integration documentation and release evidence.

Standalone product development belongs in the respective product repositories.

## Architecture

The canonical native workspace is **`kai-os/Cargo.toml`**. It currently defines 11 Rust workspace members. The repository does not have a root `Cargo.toml`.

```text
ATCLang
   │
   ▼
ATC-VM
   │
   ▼
A-TownChain
   │
   ├── Rust chain infrastructure
   └── ecosystem services
          │
          ▼
      ShivaCore
      (kernel / TCB)
          │
          ▼
      GlobusOS
      (operating system)
          │
          ▼
      Aurora AI
      (AI layer)
          │
          ▼
a-townchain-os
(integration / orchestration)
```

The exact runtime dependency direction is defined by the component specifications. The diagram describes architectural roles, not an assertion that every component is linked into every build.

Key integration components include:

- `kai-os/` — Rust workspace for the KAI-OS integration/runtime components;
- GitHub Actions governance, integration and release gates;
- Windows packaging and signing scripts;
- documentation and integration tests.

There is currently no root `scripts/sync_modules.py`; documentation must not imply that absent tooling exists.

### Repository boundaries

- `atclang` — language and compiler layer.
- `atc-vm` — deterministic execution boundary.
- `a-townchain` — sovereign deterministic blockchain/L1.
- `atc-shivacore` — reusable kernel/TCB; canonical kernel integration is maintained by `globus-os`.
- `globus-os` — operating-system userspace/platform.
- `aurora-ai` — AI services and agent layer.
- `a-townchain-os` — integration and orchestration.

## Features

- Integrated Rust workspace for KAI-OS runtime components.
- Deterministic state, synchronization and networking components with integration tests.
- Governance, dependency-review and release verification workflows.
- Windows x64 packaging with signing, checksums, SBOM and build-provenance gates.
- Machine-readable ATC repository metadata and evidence tracking.

## Installation

Clone the repository and use the canonical `kai-os` workspace:

```bash
git clone https://github.com/A-TownChain-Okosystems/a-townchain-os.git
cd a-townchain-os/kai-os
cargo build --workspace --locked
```

For local quality checks:

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo test --workspace --locked
cargo audit --deny warnings
```

Windows release packaging additionally requires the toolchain documented in `packaging/windows/`.

## Development

Development follows `ATC-STD-000` and the applicable repository standards. Architecture changes must use the organization's approved change/decision process.

Contributors must read `CONTRIBUTING.md` and `AGENTS.md` before changing the repository.

## Testing

```bash
cd kai-os
cargo test --workspace --locked
```

Additional integration, governance and release tests are defined by the current CI configuration.

A passing test run is evidence for those tests only; it does not automatically establish an audit or `PRODUCTION_READY` state.

## Security

Security-sensitive vulnerabilities must not be disclosed through public GitHub Issues. Follow `SECURITY.md` and the approved ATC security-disclosure process.

The release pipeline is designed to fail closed before publication: formatting, clippy, locked tests, RustSec auditing, signed artifacts, signature verification, SHA-256 checksums, SBOM and build-provenance gates are defined in `.github/workflows/kai-os-release.yml`. Runtime and independent security verification are still required.

## Roadmap

The current roadmap and production gates are maintained in `ROADMAP.md`. Repository readiness remains independent from governance approval, implementation status, audit status and release status.

## Version

The canonical repository version is `0.1.0` and is declared in `.atc/repository.yaml`. Release tags and the KAI-OS node crate version must remain consistent with the release workflow's version-consistency gate.

## Compliance terminology

- **APPROVED** — formal governance approval.
- **IMPLEMENTED** — implementation exists.
- **AUDITED** — relevant audit evidence exists.
- **PRODUCTION_READY** — all required production/release gates passed.

No status is inferred from another status.

## Documentation

- `ARCHITECTURE.md` — integration architecture.
- `STATUS.md` — current repository status.
- `ROADMAP.md` — repository roadmap.
- `docs/` — integration documentation and audit evidence.
- `a-townchain-os-docs` — ecosystem documentation/wiki repository.

## Repository Structure

```text
.
├── .atc/
├── .github/
├── docs/
├── kai-os/
├── packaging/
├── tests/
├── AGENTS.md
├── AGENT_MANIFEST.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── README.md
├── ROADMAP.md
├── SECURITY.md
├── STATUS.md
└── SPEC-DRAFT-AIP-001.md
```

The repository tree and manifests remain authoritative; generated inventories are subordinate evidence and must be regenerated when the tree changes.

## Contributing

Read `CONTRIBUTING.md` and `AGENTS.md` before contributing. Changes must satisfy the applicable CI and governance gates.

## License

Apache License 2.0. See `LICENSE`.

## Repository Metadata

<!-- atc metadata block (ATC-STD-README-001 §14) -->
<!--
atc:
  standard: ATC-STD-README-001
  version: 1.0.0
repository:
  id: ATC-REPO-OS-001
  name: a-townchain-os
  type: integration
  status: development
ownership:
  organization: A-TownChain-Okosystems
technology:
  primary_language: Rust
  workspace: kai-os/Cargo.toml
governance:
  criticality: CRITICAL
-->
