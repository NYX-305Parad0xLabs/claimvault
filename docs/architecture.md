# Architecture Overview

ClaimVault balances a lean FastAPI backend with a typed Next.js frontend and shared contracts so every case-building action stays observable. The key principles are:

- **Domain-first design:** SQLModel entities, routers, services, and readiness rules are expressed in terms of Claim-Vault concepts (users, workspaces, cases, evidence, exports, audits).
- **Lifecycle wiring:** create_app builds services, storage, packagers, and structured logging inside the FastAPI lifespan so there are no import-time side effects; pp.state exposes the engine, session factory, services, and config for routers.
- **Guarded surfaces:** scripts/check_imports.py verifies the pp package can load without executing business logic, while make ci bundles Ruff, pytest, migrations, frontend lint/typecheck, and the import guard.

## System Context
`mermaid
flowchart LR
  Browser["Next.js App Shell"]
  API["FastAPI API"]
  DB["SQLite / SQLModel"]
  Storage["Local evidence & export storage"]
  Contracts["packages/contracts JSON schemas"]
  Packager["VaultPackager seam (default zip / Liquefy stub)"]
  Browser --> API
  API --> DB
  API --> Storage
  API --> Contracts
  API --> Packager
`

## Domain Entities
| Entity | Description |
| --- | --- |
| User | Email/password identity tied to a role and workspace membership for RBAC. |
| Workspace | Tenant boundary that owns cases, evidence, audits, and exports. |
| Case | Core claim with workflow status, claim type, counterparty/merchant metadata, amounts, dates, and audit timestamps. |
| EvidenceItem | Files or notes attached to a case with storage keys, SHA-256 hashes, MIME metadata, and extracted text. |
| TimelineEvent | Append-only chronological log for status transitions, notes, and manual annotations recorded with actors and metadata. |
| CaseExport | Export record storing bundle paths and metadata for deterministic proof generation. |
| AuditEvent | Append-only spine capturing entity_type, entity_id, ction, ctor, and structured metadata for every significant mutation. |

## API Surface Summary
| Route | Purpose |
| --- | --- |
| GET /healthz, GET /version | Operational signals for uptime and deployment metadata. |
| POST /api/auth/register, POST /api/auth/login, GET /api/auth/me | Workspace-aware auth with JWTs and roles (owner/operator/viewer). |
| POST /api/cases, GET /api/cases, GET /api/cases/{id} | Case CRUD with filters, pagination, and explicit domain validation via contracts. |
| PATCH /api/cases/{id} | Updates case details but never mutates workflow state without transition endpoints. |
| POST /api/cases/{id}/transition | Workflow transitions with guarded state machine, timeline events, and audit writes. |
| GET /api/cases/{id}/readiness | Missing-evidence analyzer returning scores, missing/optional items, and blockers. |
| POST /api/cases/{id}/timeline-events, GET /api/cases/{id}/timeline, POST /api/cases/{id}/notes | Manual event recording with append-only semantics and note attachments. |
| POST /api/cases/{id}/evidence, GET /api/cases/{id}/evidence, GET /api/evidence/{id}/download | Evidence ingestion, listing, metadata, and download with hashed files and storage interface. |
| POST /api/cases/{id}/exports, GET /api/cases/{id}/exports/{export_id}/download | Deterministic proof bundles with manifest/hash files plus zipped evidence, logged via audit and timeline. |
| GET /api/cases/{id}/audit-events | Audit log surface for UI trust, sorted by timestamp and filtered by workspace. |

## Services & Lifespan
create_app builds settings, a structured logger, the SQLModel engine/session factory, storage adapters, and the Services container (AuditService, AuthService, CaseService, EvidenceService, ExportService, ReadinessService, TimelineService). The lifespan context initializes shared structures, registers them on pp.state, and ensures the logger notes when the app starts/stops. Routers take dependencies from pp.state.services, so there are no import-time side effects.

## Storage & Vault Packager
LocalEvidenceStorage and LocalExportStorage keep files under CLAIMVAULT_DATA_DIR, scoped by workspace and case. Each upload recalculates a SHA-256 hash and records metadata so downloads can validate integrity. Exports rely on the VaultPackager interface; the default implementation zips summary.md, case.json, 	imeline.json, evidence_manifest.json, checksums.txt, and the evidence files with deterministic ordering. A LiquefyPackager stub lives alongside the default version, and the runtime switch (VAULT_PACKAGER env) determines which implementation is wired.

## Contracts & Guardrails
packages/contracts holds JSON schemas for every request and response shape. FastAPI uses them to validate payloads, while the Next.js typed client consumes the same folder so the UI speaks the same language as the API. The import-check guard, the make ci target, and the GitHub Actions workflow ensure Ruff, pytest, migrations, frontend lint/typecheck, and import-time safety stay green before merging.
