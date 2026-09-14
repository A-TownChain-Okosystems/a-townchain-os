# ATC A-TownChain OS

> Integration monorepo for assembling and validating the A-TownChain ecosystem.

**Project:** `a-townchain-os`  
**Organization:** `A-TownChain-Okosystems`  
**Status:** `development`  
**Version:** `0.1.0`  
**License:** `Apache-2.0`  
**Standard:** `ATC-STD-README-001`

## Overview

`a-townchain-os` is the central integration and orchestration repository. It brings together the ecosystem's product repositories, workspace components, launch/integration tooling, CI/CD and governance validation.

It is an **integration layer**, not a replacement for the individual canonical repositories.

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

## Scope

This repository covers integration concerns such as:

- Cargo workspace integration where configured.
- Module synchronization tooling.
- CI/CD and governance workflows.
- Docker/launch integration where present.
- Cross-repository validation and system-level tests.
- Integration documentation and release evidence.

Standalone product development belongs in the respective product repositories.

## Status

`development` is the authoritative repository status stated here. Historical rebuild milestones, test counts, audit records or claims from earlier architecture versions are not treated as current production guarantees.

There is no Mainnet or Production claim in this README. `APPROVED`, `IMPLEMENTED`, `AUDITED`, and `PRODUCTION_READY` remain independent states.

## Architecture

Key integration components include:

- Cargo workspace and Rust integration crates where present.
- Docker/Compose launch tooling where present.
- `scripts/sync_modules.py` for repository/module synchronization where present.
- GitHub Actions governance and CI gates.
- Documentation and integration tests.

### Repository boundaries

- `atclang` — language and compiler layer.
- `atc-vm` — deterministic execution boundary.
- `a-townchain` — sovereign deterministic blockchain/L1.
- `atc-shivacore` — reusable kernel/TCB.
- `globus-os` — operating-system userspace/platform.
- `aurora-ai` — AI services and agent layer.
- `a-townchain-os` — integration and orchestration.

## Quick Start

```bash
git clone https://github.com/A-TownChain-Okosystems/a-townchain-os.git
cd a-townchain-os

cargo build --workspace
cargo test --workspace
```

If Python integration tooling is required by the current checkout:

```bash
python3 scripts/sync_modules.py --check
```

Use the repository's current manifests and documentation for component-specific prerequisites.

## Requirements

- Rust toolchain for Rust workspace components.
- Python 3.11+ for Python tooling where configured.
- Docker/Compose where the launch stack is enabled.
- Git.

## Testing

```bash
cargo test --workspace
```

Additional integration and governance tests are defined by the current CI configuration.

A passing test run is evidence for those tests only; it does not automatically establish an audit or `PRODUCTION_READY` state.

## Development & Governance

Development follows `ATC-STD-000` and the applicable repository standards. Architecture changes must use the organization's approved change/decision process.

Canonical standards use family-scoped IDs:

```text
ATC-STD-F{family}-{sequence}
```

Legacy IDs remain preserved during migration. IDs must not be silently renumbered, reused, or allocated outside the standards registry and governance process.

## Compliance terminology

- **APPROVED** — formal governance approval.
- **IMPLEMENTED** — implementation exists.
- **AUDITED** — relevant audit evidence exists.
- **PRODUCTION_READY** — all required production/release gates passed.

No status is inferred from another status.

## Security

Security-sensitive vulnerabilities must not be disclosed through public GitHub Issues. Follow `SECURITY.md` and the approved ATC security-disclosure process.

## Documentation

- `ARCHITECTURE.md` — integration architecture.
- `STATUS.md` — current repository status.
- `ROADMAP.md` — repository roadmap.
- `docs/` — integration documentation.
- `a-townchain-os-docs` — ecosystem documentation/wiki repository.

## Repository Structure

```text
.
├── .atc/
├── .github/
├── docs/
├── scripts/
├── src/
├── tests/
├── Cargo.toml
├── ARCHITECTURE.md
├── AGENTS.md
├── CHANGELOG.md
├── LICENSE
├── README.md
├── ROADMAP.md
├── SECURITY.md
└── STATUS.md
```

Directories or files not present in a particular checkout are not implied by this documentation; the repository tree and manifests remain authoritative.

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
  primary_language: Rust/Python
governance:
  criticality: CRITICAL
-->
