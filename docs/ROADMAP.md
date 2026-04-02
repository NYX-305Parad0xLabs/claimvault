# Roadmap

ClaimVault advances through measured phases so the product stays trustworthy while the backlog grows.

## Phase 0 â€“ Foundation (complete)
- FastAPI app factory with settings, structured logging, services, and lifespan wiring.
- Next.js App Router shell with typed API client scaffolded from packages/contracts.
- Domain models for users, workspaces, cases, evidence, timeline events, exports, and audit entries.
- Guardrails: .env templates, import-check script, Makefile targets, and CI-ready layouts.

## Phase 1 â€“ Case building and workflows (shipping)
- Auth + RBAC with JWTs, password hashing, current-user dependency, and workspace membership checks.
- Case CRUD plus workflows via /api/cases/{id}/transition, timeline events, notes, and evidence ingestion.
- Readiness analyzer scoring cases for missing evidence, optional items, and export blockers.
- Frontend listing/detail flows, audit tab, readiness panel, note creation, and upload UX.

## Phase 2 â€“ Proof exports and audit trust
- Deterministic export bundles with summary, timeline, evidence manifest, checksums, and zipped files.
- Audit and timeline surfaces that appends every transition, upload, and export with human-readable metadata.
- Frontend download flows, audit tab, and export visibility to let operators leave the platform with verifiable proof.

## Phase 3 â€“ Liquefy, automation, and trust services
- VaultPackager keeps the export surface swap-able via `VAULT_PACKAGER`, letting Liquefy take over verified packing, vault search, policy/redaction, proof artifact generation, and safe restore without changing the public API.
- Liquefy adapter implements the `LiquefyPackager` stub, emits clean warnings/extensibility hooks, and defers to the external repo until the integration ships.
- Automation hooks replay audits, readiness rules, and exports so the platform can coordinate with Liquefy's agents.

For each phase, update docs/ARCHITECTURE.md and docs/SECURITY_MODEL.md so reviewers understand how data flows and what risks are mitigated. Branch protection (see docs/GOVERNANCE.md) keeps these releases safe.
