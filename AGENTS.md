# AI Agent Instructions

## Identity
Dieser Bereich definiert die Regeln und Workflows für KI-Agenten, die in `a-townchain-os` arbeiten. Maßgebliche Standards: ATC-STD-000, ATC-STD-README-001, ATC-STD-MD-001, ATC-AAS-001..025.

## Entry Point
1. [README.md](README.md) — Identität, Zweck und Übersicht
2. [STATUS.md](STATUS.md) — Aktueller System- und Gate-Status
3. [ARCHITECTURE.md](ARCHITECTURE.md) — Systemarchitektur L7
4. [ROADMAP.md](ROADMAP.md) — Meilensteine M1–M8
5. [CHANGELOG.md](CHANGELOG.md) — Änderungshistorie

## Required Workflow
1. **Status prüfen:** Inspect `STATUS.md` and active issues.
2. **Standards lesen:** Verify applicable standards in `atc-standards`.
3. **Architektur inspizieren:** Align with `ARCHITECTURE.md` and L7 boundaries.
4. **Aufgabe umsetzen:** Implement changes following Conventional Commits.
5. **Tests & Doku:** Run `cargo test --workspace` and update documentation.
6. **Konsistenz prüfen:** Execute `check_readme.py` and `check_md.py` validators.
