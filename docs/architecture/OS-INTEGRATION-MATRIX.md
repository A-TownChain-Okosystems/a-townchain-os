---
document_id: ATC-DOC-OS-INT-001
title: "OS Operations & Integration Traceability Matrix"
version: 1.0.0
status: active
owner: A-TownChain-Okosystems
created: 2026-09-30
updated: 2026-09-30
standard: ATC-STD-MD-001
---

# OS Operations & Integration Traceability Matrix

## Purpose

This document makes the operating-system integration boundary explicit and traceable. It is an implementation and verification contract, not a claim that every listed connection already exists.

The canonical path is:

`UEFI/BIOS → Secure Boot → ShivaCore → Kernel → HAL/Drivers → GlobusOS Services → Identity/Capability/Policy → Storage/Network/GPU/NPU → Aurora/Kai → Applications → User`

## Evidence semantics

The following states are distinct and must never be collapsed:

- **DISCOVERED** — repository/source evidence identifies the element.
- **IMPLEMENTED** — implementation evidence establishes that the element exists as executable behavior.
- **TESTED** — relevant tests exist and have execution evidence.
- **CI VERIFIED** — the exact commit SHA has corresponding CI evidence.
- **VERIFIED** — the required evidence chain is complete for the stated scope.
- **RESIDUAL** — a concrete gap remains.

`Architecture ≠ Implementation ≠ Test ≠ CI Evidence ≠ Verification`

`Architecture Connection ≠ Implemented Connection ≠ Tested Connection ≠ CI-Verified Connection`

`Source vorhanden ≠ Implementiert ≠ Verifiziert`

For SCR-0129:

`Error Evidence ≠ Finding Evidence ≠ Verification Evidence`

## Connection contract

Every integration edge is represented by:

| Field | Requirement |
|---|---|
| Source Component | Canonical originating component |
| Target Component | Canonical receiving component |
| Direction | Source → Target |
| Interface / API | Named interface or boundary |
| Contract ID | Stable contract/specification identifier |
| Protocol | Wire/runtime mechanism |
| Input | Input semantics |
| Output | Output semantics |
| Data Type / Encoding | Canonical representation |
| AuthN / AuthZ | Authentication and authorization requirements |
| Dependency | Required upstream dependency |
| Runtime Boundary | Kernel / process / service / VM / external boundary |
| Failure / Error Handling | Fail-closed/error semantics |
| Test | Required test class |
| CI Workflow | Workflow that executes the relevant test |
| Exact SHA | Commit-specific CI identity |
| Evidence | Run → Job → Ergebnis → Step → Exit code → Log |
| Verification | Verification result |
| Residual | Remaining gap |

## Canonical OS integration matrix

| ID | Source | Target | Interface / Contract | Runtime Boundary | Required Verification | Status |
|---|---|---|---|---|---|---|
| OS-INT-001 | UEFI/BIOS | ShivaCore | Boot handoff / kernel entry contract | Firmware → TCB | Boot/QEMU evidence | RESIDUAL |
| OS-INT-002 | Secure Boot | ShivaCore | Verified boot / trust-chain contract | Firmware → TCB | Secure-boot verification | RESIDUAL |
| OS-INT-003 | ShivaCore | Kernel | Kernel ABI / capability boundary | TCB → kernel | Kernel tests + exact-SHA CI | RESIDUAL |
| OS-INT-004 | Kernel | CPU/Memory/Interrupts | HAL / architecture interface | Kernel → hardware | Hardware/QEMU smoke | RESIDUAL |
| OS-INT-005 | Kernel | Scheduler | Process/scheduling contract | Kernel | Scheduler tests | RESIDUAL |
| OS-INT-006 | Kernel | IPC | IPC ABI / message contract | Kernel → processes | IPC integration tests | RESIDUAL |
| OS-INT-007 | HAL | Drivers | Device interface | Kernel → driver | Driver tests | RESIDUAL |
| OS-INT-008 | Drivers | Storage | Block/storage API | Kernel → device | Storage/recovery tests | RESIDUAL |
| OS-INT-009 | Drivers | Network | Network device API | Kernel → device | Network integration tests | RESIDUAL |
| OS-INT-010 | Drivers | GPU/NPU | Accelerator HAL | Kernel → accelerator | Accelerator smoke/evidence | RESIDUAL |
| OS-INT-011 | GlobusOS Core | System Services | OS service API | Process/service | Integration tests | RESIDUAL |
| OS-INT-012 | Identity | Authentication | AuthN contract | Service boundary | AuthN tests | RESIDUAL |
| OS-INT-013 | Authentication | Session | Session lifecycle contract | Service boundary | Session/recovery tests | RESIDUAL |
| OS-INT-014 | Identity | Authorization | AuthZ / RBAC-ABAC / capability contract | Service boundary | Policy tests | RESIDUAL |
| OS-INT-015 | Authorization | ShivaCore | Capability ABI | Service → TCB | Capability enforcement evidence | RESIDUAL |
| OS-INT-016 | VFS | Applications | Filesystem API | Service/process | VFS integration tests | RESIDUAL |
| OS-INT-017 | Network Stack | Applications | Socket/service API | Service/process | Network E2E | RESIDUAL |
| OS-INT-018 | GPU | Desktop/Applications | Display/graphics API | Device → process | Graphics smoke | RESIDUAL |
| OS-INT-019 | NPU/GPU | Aurora Runtime | Accelerator API | Device → AI runtime | AI hardware evidence | RESIDUAL |
| OS-INT-020 | GlobusOS | Aurora/Kai | OS capability/tool API | Process/service | Policy + IPC E2E | RESIDUAL |
| OS-INT-021 | Aurora/Kai | Blockchain services | Node/RPC capability contract | Process/service | Blockchain integration E2E | RESIDUAL |
| OS-INT-022 | Package Repository | Package Manager | Artifact/package contract | External → OS | Signature/integrity tests | RESIDUAL |
| OS-INT-023 | Package Manager | Update/Recovery | Update lifecycle contract | Service/system | Recovery/rollback tests | RESIDUAL |
| OS-INT-024 | Kernel/Services | Audit | Structured audit contract | TCB/service → audit | Audit integrity tests | RESIDUAL |
| OS-INT-025 | Developer SDK | OS APIs | Stable developer API contract | Tool → service | SDK integration tests | RESIDUAL |

## Identity & Access integration

Login and registration are first-class system integrations, not UI-only features.

| ID | Source | Target | Function | Required boundary |
|---|---|---|---|---|
| IAM-001 | User | Identity Service | Registration / account creation | Application → identity |
| IAM-002 | User | Identity Service | Login / authentication | Application → identity |
| IAM-003 | Identity Service | Session Manager | Session creation/renewal/revocation | Service → service |
| IAM-004 | Credential/Key Store | Identity Service | Credential/key lifecycle | Secure storage boundary |
| IAM-005 | Identity | Authorization | AuthN → AuthZ handoff | Service boundary |
| IAM-006 | Authorization | Capability Engine | Permission/capability evaluation | Policy boundary |
| IAM-007 | Identity | Wallet | Blockchain identity binding | Identity → wallet |
| IAM-008 | Wallet | SDK | Authenticated transaction signing | Wallet → SDK |
| IAM-009 | API/RPC Client | API/RPC | Request authentication | External/service boundary |
| IAM-010 | Identity/Security | Audit | Authentication and authorization events | Audit boundary |
| IAM-011 | Recovery | Identity | Account lifecycle recovery | Recovery boundary |

Required flow:

`User → Registration → Identity → Account/Wallet → Authentication → Session → Authorization → Application/API → Audit`

Blockchain flow:

`User → Login → Identity → Wallet → Transaction Signing → SDK → Node`

## AI security boundary

The canonical AI authority chain is:

`Model → Agent → Capability → Policy → Approval → Tool → GlobusOS → ShivaCore`

Model output is never itself an authorization source. AI-originated OS or blockchain actions require explicit capability/policy enforcement and, where specified, approval.

Existing KAI-OS runtime components provide relevant implementation candidates, including capability enforcement, IPC schema validation, replay protection and audit chaining. Their presence is discovery/implementation evidence only; integration verification remains separate.

## Verification record

For every connection that reaches CI verification, record:

`Run → Job → Ergebnis → Step → Exit code → Log → Source → RCA → Minimal Fix → Commit → Rerun`

No connection may be marked **VERIFIED** without exact-SHA evidence for the relevant scope.

## Residuals

The following are intentionally explicit until evidence closes them:

1. Hardware/UEFI/Secure-Boot execution evidence is not inferred from source presence.
2. Cross-repository OS ↔ ShivaCore ↔ Aurora ↔ blockchain runtime connections require integration evidence.
3. Login/registration implementation must be traced to actual identity/authentication code before being marked IMPLEMENTED.
4. A complete repository-wide function inventory still requires AST/symbol indexing; code search is only a discovery baseline.
5. CI status is commit-specific; historical workflow results do not establish current-main verification.
