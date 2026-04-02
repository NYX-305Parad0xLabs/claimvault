# ClaimVault

Messy evidence in → verified case package out.

ClaimVault is the verified evidence and dispute operating system for operations teams chasing refunds, warranties, chargebacks, damaged shipments, and move-out disputes. It ingests receipts, emails, photos, notes, and uploaded files, builds a timeline and missing-evidence checklist, and exports auditable proof bundles with hashed documents and append-only logs.

## Who it is for
- Customer ops teams that must prove refunds, warranty claims, or chargeback defenses with tight audit trails.
- Compliance owners who need a single-pane timeline that ties evidence, timeline notes, readiness scores, and exports together.
- Internal review squads that want deterministic case data for external partners (e.g., Liquefy) without relying on manual spreadsheets.

## MVP snapshot
- FastAPI core case engine with SQLModel, migrations, JWT auth, workspace RBAC, and ALEMBIC-managed schema.
- Evidence ingestion, timeline events, readiness analyzer, audit spine, and deterministic proof exports (summary + manifest + checksums + zipped evidence).
- Next.js App Router UI with typed API client, login/register flows, case list/detail screens, readiness panels, audit tabs, and evidence upload/download.
- Guardrails for local dev: .env templates, scripts/check_imports.py, Makefile targets, and GitHub Actions running Ruff, pytest, migrations, lint, typecheck, and the import guard.

## Architecture at a glance
### Core case engine
Cases are SQLModel entities that capture metadata (claim type, workflow status, financials, dates) scoped to workspaces. Mutations go through services that enforce transitions, emit audit events, and trigger readiness scoring.
### Evidence timeline
Every upload, note, or manual event is appended to the timeline. Timeline events and evidence items share metadata, tags, hashes, and audit entries so investigators can follow the story in order.
### Readiness rules
The readiness analyzer runs claim-type‑specific rule sets (return, warranty, chargeback, damaged shipment, rental dispute). It returns a score, missing required items, optional recommendations, and blockers that must be resolved before exports.
### Proof bundle export
Export service bundles summary.md, case.json, 	imeline.json, evidence_manifest.json, and checksums.txt plus the evidence files. The VaultPackager interface keeps exports deterministic and ready for future partners.
### Audit spine
Every action that touches a case (status transition, evidence upload, export generation, auth events) writes an append-only AuditEvent with actor, timestamp, entity type, and metadata. The UI surfaces these events on the case detail audit tab.
### Future integrations
Liquefy: drop-in packing/search/proof artifact partner once the VaultPackager seam receives real APIs.
NULLA: workflow assistant that can trigger notes, readiness reminders, or evidence requests via the existing service surface.
DNA anchoring: paid exports will embed cryptographic anchors and metadata in the manifest so downstream verifiers can trust the package.

## Quickstart
1. Clone the repo and drop into it: git clone git@github.com:NYX-305Parad0xLabs/claimvault.git && cd claimvault.
2. Copy configuration samples: cp .env.example .env, cp apps/api/.env.example apps/api/.env, cp apps/web/.env.example apps/web/.env.
3. Install dependencies: make install (or scripts/bootstrap.sh / scripts/bootstrap.ps1).
4. Run make ci to exercise Ruff, pytest, migrations, frontend lint/typecheck, and the import guard.
5. Start the services with make api-dev and make web-dev.

## Supporting docs
- docs/POSITIONING.md – product message, buyer cues, and outcomes.
- docs/USE_CASES.md – concrete use cases (refunds, warranties, chargebacks, damage, rentals).
- docs/NON_GOALS.md – clearly call out what is outside the MVP.
- docs/ARCHITECTURE.md – deeper technical context and future-proof details.
- docs/MVP_CHECKLIST.md – release-ready checklist of what is finished and what is tracked for later.
- docs/SECURITY_MODEL.md / docs/GOVERNANCE.md – authentication/audit controls and required CI sweeps.
