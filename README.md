# a-townchain-os — REBUILD

Dieses Repository wird neu aufgebaut (Owner-Entscheidung 06.09.2026, AD-018).

**Gesamtvault:** Der komplette Stand vor dem Abbau (Launch-Stack mit
docker-compose, 60 Module, 2.157 Dateien, Commit 8606e50 inkl.
ATCLang-Topologie-Fix) liegt strukturgetreu im Wiki-Repository:
[a-townchain-os-docs/docs/archive/monorepo-full/](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs/tree/main/docs/archive/monorepo-full)

**Launch-Zeitpunkt:** Per AD-023 kein Termin — qualitaetsgetriebener Rebuild
(atc-shivacore SC-001+ → Produkt-Repos; Launch-Stack bei Bedarf aus dem Vault).

Rebuild-Fortschritt: atclang abgeschlossen (AD-019, Phase 1).

---

## ATC Compliance & Governance (ATC-STD-201 / 202 / 203)

**ATC COMPLIANCE: R3** — auditiert am 2026-09-07 (atc-repo-audit; R-Level aus `.atc/repository.yaml`).
Architekturentscheidungen: zentral im [DECISIONS_REGISTER](https://github.com/A-TownChain-Okosystems/a-townchain-os-docs/blob/main/docs/DECISIONS_REGISTER.md) (AD-Nummern verbindlich; lokale Entscheidungen in `docs/decisions/`).

- **Purpose:** Integrations-Monorepo (L7): Cargo-Workspace, Launch-Stack, CI/CD.
- **Scope:** Layer L7, Domain integration — a-townchain-os als INFRA in der 23-Repo-Landschaft (AD-024/026).
- **Architecture:** Module kommen via scripts/sync_modules.py aus den Produkt-Repos (AD-017: Produkt gewinnt); Cargo-Workspace 19+ Crates; Docker 10 Dienste; CI ci.yml + codeql.yml.
- **Features:** 731/731 Workspace-Tests + Kernel 674/674; Prometheus/Grafana-Monitoring.
- **Installation:** Modul-Build je Sprache (rust); Integration via Monorepo-Workspace (a-townchain-os, sync_modules.py).
- **Development:** Conventional Commits; Governance-Regeln aus atc-standards; Naming gemaess ATC-STD-000 §7.
- **Testing:** cargo test --workspace: 731/731; CI laeuft (ci.yml, codeql.yml).
- **Security:** SECURITY.md; S-Klasse S3; ATC-STD-203 Release-Gates; Emergency-Prozess ATC-STD-000 §32.
- **Roadmap:** Einordnung in die Lauffaehigkeits-Roadmap M1-M8 (AD-027) und Bauhierarchie L0-L7 (AD-026).
- **Version:** CHANGELOG.md; SemVer; Releases als ATC-REL-X.Y.Z.
- **License:** Proprietaer — All Rights Reserved, Michael Wroblewski / ShivaCore / A-TownChain-Okosystems (ATC-LIC/ATS-LIC).
