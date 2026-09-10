# ATC A-TownChain OS

> Integrations-Monorepo (L7) des A-TownChain-Ökosystems für Cargo-Workspace, Launch-Stack, CI/CD und Modul-Orchestrierung.

**Project:** a-townchain-os
**Organization:** A-TownChain-Okosystems
**Status:** `development`
**Version:** `0.1.0`
**License:** `Apache-2.0 — A-TownChain-Okosystems`
**Standard:** `ATC-STD-README-001`
**Maintainer:** A-TownChain-Okosystems (ShivaCoreDev)

> **ATC COMPLIANCE: R3 · Standard ATC-STD-201 v1.0.0 · GATE: AUDITED (07.09.2026) · README: ATC-STD-README-001 CONFORM (13/13)**

<!-- atc metadata block (ATC-STD-README-001 §14) -->
<!--
atc:
  standard: ATC-STD-README-001
  version: 1.0.0
repository:
  id: ATC-REPO-OS-001
  name: a-townchain-os
  type: software
  status: development
ownership:
  organization: A-TownChain-Okosystems
technology:
  primary_language: Rust / Python / Docker
governance:
  security_class: S3 — Infra & Core
  criticality: CRITICAL (L7 Integration Monorepo)
-->

## Overview

a-townchain-os ist das zentrale Integrations-Monorepo (Layer L7) des A-TownChain-Ökosystems. Nach der Rebuild-Entscheidung vom 06.09.2026 (AD-018) wird das Repository qualitätsgetrieben neu aufgebaut. Der komplette Launch-Stack vor dem Abbau (2.157 Dateien, 60 Module) liegt gesichert im Wiki-Repository unter `a-townchain-os-docs/docs/archive/monorepo-full/`.

## Purpose

ATC A-TownChain OS provides the canonical integration monorepo and orchestration environment within the A-TownChain ecosystem. It is responsible for:

- Orchestrierung des Cargo-Workspaces (19+ Crates) und des Docker-Launch-Stacks (10 Dienste)
- Automatische Modul-Synchronisation aus den Produkt-Repositories via `scripts/sync_modules.py` (Prinzip: Produkt gewinnt, AD-017)
- Bereitstellung der zentralen CI/CD-Pipelines (`ci.yml`, `codeql.yml`, `governance-ci.yml`)
- Laufzeit-Monitoring und Telemetrie (Prometheus / Grafana)

Davon hängen die Produkt- und Service-Komponenten des A-TownChain-Ökosystems für die finale L7-Systemintegration ab.

## Scope

- **Gilt für:** Layer L7 (Domain Integration), INFRA-Klassifizierung in der 27-governed-Repository-Landschaft (28 total, ai/org-scope.yaml) (AD-024/AD-026), Cargo-Workspace, Docker Launch-Stack und CI/CD-Pipelines.
- **Nicht-Gilt für:** Standalone-Entwicklung einzelner Produkt-Crates (findet in den jeweiligen Produkt-Repos statt).

## Status

**Status:** `development` — Qualitätsgetriebener Rebuild ohne starren Launch-Termin (AD-023). ATCLang-Integration abgeschlossen (AD-019 Phase 1). R3 Audit-Maturity bestätigt (07.09.2026).

## Architecture

### Components

- `Cargo Workspace`: Multi-Crate Rust Workspace (19+ Crates, Kernel atc-shivacore)
- `Docker Launch-Stack`: Orchestrierung von 10 Systemdiensten
- `Sync-Engine`: `scripts/sync_modules.py` für Modul-Synchronisation
- `CI/CD Gatekeeper`: GitHub Actions Workflows für Qualitäts- und Governance-Gates

### Data Flow

Produkt-Repositories → `sync_modules.py` → Monorepo Workspace → Cargo Test Suite (731 Tests) / Kernel (674 Tests) → Docker Launch-Stack → Release / CI Deployment.

### Dependencies

| Component | Purpose | Required |
|---|---|---|
| atc-shivacore | Layer L1 Blockchain Kernel | Yes |
| atc-vm | Layer L3 Execution VM (ATVM) | Yes |
| atc-standards | Normative Governance & Validator Suite | Yes |
| scripts/sync_modules.py | Modul-Synchronisation | Yes |

## Features

- Integrations-Workspace für 19+ Rust Crates
- Automatische Synchronisation von Modulen per CLI-Tooling
- Integriertes Prometheus/Grafana Monitoring
- 731/731 Workspace-Tests und 674/674 Kernel-Tests passing
- CI-Gates für CodeQL, Dependency Checks und Governance Audit (R3)

## Repository Structure

```text
.
├── docs/                # Projektdokumentation und Richtlinien
└── tests/               # Integrationstests und Test-Suiten
```

## Requirements

- Rust >= 1.75 toolchain (cargo, rustc)
- Python >= 3.11 (PyYAML) für Skripte
- Docker & Docker Compose v2
- Git >= 2.30

## Installation

### Setup

```bash
git clone https://github.com/A-TownChain-Okosystems/a-townchain-os.git
cd a-townchain-os
cargo build --workspace
```

## Configuration

Die Workspace-Konfiguration erfolgt über `Cargo.toml` in der Repository-Wurzel sowie Metadaten in `.atc/repository.yaml`.

## Usage

Workspace bauen und testen:

```bash
cargo build --workspace
cargo test --workspace
```

Modul-Synchronisation ausführen:

```bash
python3 scripts/sync_modules.py --check
```

## Development

Entwicklungsregeln folgen den A-TownChain Standards (ATC-STD-000 §7, ATC-STD-201). Commits MÜSSEN als Conventional Commits verfasst werden. Änderungen an Modulen erfolgen in den jeweiligen Produkt-Repositories (AD-017: Produkt gewinnt).

## Testing

Run the complete workspace test suite:

```bash
cargo test --workspace
```

Expected result: PASS (731/731 Workspace-Tests, 674/674 Kernel-Tests bestanden).

## Security

Security issues must not be disclosed publicly through GitHub Issues.

Schwachstellen werden NICHT öffentlich über GitHub Issues gemeldet, sondern direkt über den offiziellen ATC-Security-Reporting-Prozess (ATC-STD-203, [SECURITY.md](SECURITY.md)). Notfall-Prozeduren folgen ATC-STD-000 §32.

## Documentation

- `docs/REPOSITORY_STANDARD.md` — Lokale Standards und Zwei-Ebenen-Entscheidungsmodell (AD-029)
- `ARCHITECTURE.md` — Architektur-Spezifikation (Layer L7)
- `STATUS.md` — Maschinenlesbarer Projektstatus
- `ROADMAP.md` — Lauffähigkeits-Roadmap M1–M8 (AD-027)
- External Wiki: [a-townchain-os-docs](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs)

## Governance

This repository is governed according to the A-TownChain Enterprise Governance Framework (ATC-STD-000 v1.2.0, ATC-ENT-001..015). Zwei-Ebenen-Entscheidungsmodell per AD-029: Architekturentscheidungen liegen im zentralen DECISIONS_REGISTER (`a-townchain-os-docs`), lokale ADRs unter `docs/decisions/`.

## Standards & Compliance

This repository follows applicable A-TownChain standards:

| Standard | Version | Compliance |
|---|---:|---|
| ATC-STD-000 | 1.2.0 | ✅ |
| ATC-STD-201 | 1.0.0 | ✅ |
| ATC-STD-202 | 1.1.0 | ✅ |
| ATC-STD-203 | 1.0.0 | ✅ |
| ATC-STD-204 | 1.0.0 | ✅ |
| ATC-STD-README-001 | 1.0.0 | ✅ |
| ATC-STD-MD-001 | 1.0.0 | ✅ |

### Smart Contract Standards Framework (ATC-STD-SC-001..020)

Gemäß Smart Contract Standards Framework (normativ seit 07.09.2026, 21:00 UTC+2) gelten für die folgenden Token-Contracts im Ökosystem die verbindlichen SC-G0-Spec-Pflichten:

| Token Contract | Registry-ID | Standard-Verweis | Gate-Status | SC-G0-Spec-Pflicht |
|---|---|---|---|---|
| ATC-001 | ATC-SC-TOKEN-001 | ATC-STD-SC-001..020 | AUDITED | Erfüllt / Spezifikation dokumentiert |
| ATC-8300 | ATC-SC-TOKEN-002 | ATC-STD-SC-001..020 | AUDITED | Erfüllt / Spezifikation dokumentiert |
| ATC-9900 | ATC-SC-TOKEN-003 | ATC-STD-SC-001..020 | AUDITED | Erfüllt / Spezifikation dokumentiert |

## Roadmap

See the canonical roadmap:

- [ROADMAP.md](ROADMAP.md) (Lauffähigkeits-Roadmap M1–M8 per AD-027)
- GitHub Issues & Projects
- ATC Development Management (Notion Master Roadmap)

## Contributing

Beiträge erfolgen gemäß [CONTRIBUTING.md](CONTRIBUTING.md) und den Governance-Regeln von ATC-STD-000 §22. Pull Requests erfordern grünen CI-Run (`ci.yml`, `governance-ci.yml`).

## License

Apache-2.0 — A-TownChain-Okosystems. Apache-2.0, Michael Wroblewski / ShivaCore / A-TownChain-Okosystems (ATC-LIC/ATS-LIC). See [LICENSE](LICENSE).

## Maintainers

**Organization:** A-TownChain-Okosystems  
**Maintainer:** ShivaCoreDev / Aurora Superagent

## Changelog

See detailed release history in [CHANGELOG.md](CHANGELOG.md).
