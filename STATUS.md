---
document_id: ATC-DOC-ATCOS-STATUS-001
title: Repository Status — a-townchain-os
version: 1.1.0
status: active
owner: A-TownChain-Okosystems
updated: 2026-09-15
standard: ATC-STD-MD-001
---

# Repository Status — a-townchain-os

| Property | Value |
|---|---|
| Repository | a-townchain-os |
| Version | 0.1.0 |
| Status | development |
| Security Class | S3 |
| Architecture role | L7 Domain Integration / Core Runtime |
| Language boundary | Rust native infrastructure; ATCLang on-chain semantics; ATC-VM execution boundary |
| Build | NOT VERIFIED — current CI evidence required |
| Tests | NOT VERIFIED — historical test counts are not current evidence |
| Documentation | ATC-STD-README-001 / ATC-STD-MD-001 |
| Production readiness | NOT_READY |
| Current gate | GATE-KAI-001 Iteration 2 OPEN |
| Last documentation cross-check | 2026-09-15 |

## Current cross-check

The repository was cross-checked against the current organization architecture and active implementation state on 2026-09-15.

The current production-closing work is tracked by Issue #112 (GATE-KAI-001 Iteration 2). The remaining work areas are Model Registry + Verified Cache, persistent storage with WAL/snapshot/crash recovery, real TCP transport with limits/backpressure and discovery persistence, deterministic upgrade/rollback semantics, and external-security-audit preparation.

These open gate items prevent a `PRODUCTION_READY` claim. Historical statements such as fixed test counts are retained only as historical context and are not used as current evidence.

## Architecture consistency

The repository remains the L7 integration/runtime layer. It must not absorb ShivaCore kernel responsibilities, and it must not move blockchain consensus semantics into the OS runtime. AD-008 remains the language boundary: ATCLang is canonical for on-chain semantics, Rust carries native infrastructure, and ATC-VM is the execution boundary.

## Evidence policy

No PASS state is inferred from documentation alone. Current build, test, security and production claims require machine-readable evidence from the relevant current commit/CI run.
