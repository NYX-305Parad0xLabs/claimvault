# Architecture Overview

ClaimVault is a verified evidence and dispute operating system that keeps every case, evidence item, timeline event, readiness check, export, and audit entry in one codebase. The core layers are designed to be observable, testable, and extendable for future integrations.

## Core case engine
- SQLModel case entities capture workflow status, claim type (refund, warranty, chargeback, damaged shipment, rental dispute), merchant details, financials, and timeline references.
- Services enforce transition rules, guard status updates, and orchestrate side effects such as readiness recalculation, audit logging, and export generation.
- Workspaces separate data, and JWT auth plus RBAC ensures only authorized roles (owner/operator/viewer) mutate or read claims.

## Evidence timeline
- Evidence items store metadata (kind, storage key, hash, extracted text, metadata JSON) and point to cases.
- Timeline events are append-only; uploads, notes, transitions, and exports append to the same chronological trail so every decision can be traced.
- The UI and services layer consume the timeline to render contextual narratives for disputes and claims.

## Readiness rules
- Claim-type-specific rule engines return a completeness score (0-100), missing required items, recommended optional tasks, and blockers that must be cleared before exports.
- Rules run on every relevant detail fetch and after evidence uploads or timeline updates so the score reflects the latest state.
- Future automation (NULLA) can hook into the readiness results to nudge operators toward compliance.

## Proof bundle export
- ExportService builds deterministic bundles containing summary.md, case.json, timeline.json, evidence_manifest.json, checksums.txt, and the evidence files.
- `VaultPackager` abstracts packaging behind the `VAULT_PACKAGER` environment flag so the default zipper can be replaced by a Liquefy adapter in production without affecting the rest of the API.
- Bundles record metadata (hashes, actor, timestamps) so auditors can verify integrity without rerunning the case.

### Liquefy integration seam

- The `VaultPackager` surface keeps export logic deterministic while Liquefy prepares the same bundle through a separate adapter. The current stub warns when run and raises `NotImplementedError` until the external repo ships.
- Verified packing: Liquefy will confirm byte-for-byte fidelity, sign manifests, and publish tamper-indicative metadata so downstream parties can trust a bundle without rerunning ClaimVault.
- Vault search: Liquefy will index every case, evidence item, and timeline event so auditors can query proofs without stressing the FastAPI service.
- Policy and redaction: Liquefy enforces retention/redaction policies before shipping an export so sensitive evidence is protected in compliance-controlled workflows.
- Proof artifact generation: Liquefy will extend the manifest with DNA anchors, hash chains, and proof metadata ready for reuse wherever proof-of-reserve or automated claims are required.
- Safe restore: Liquefy is expected to offer a rehydration path, allowing exported bundles to be replayed into ClaimVault when rebuilding or migrating a workspace.

## Audit spine
- Every meaningful action (status transition, evidence upload, timeline note, export, register/login) writes an AuditEvent with actor, entity type, entity id, action, happened_at, and metadata.
- The audit surface filters by workspace, orders by time, and exposes human-readable insights through the UI so trust reviewers can inspect changes.

## Domain Entities
| Entity | Description |
| --- | --- |
| `User` | Platform operators/auditors with hashed credentials and workspace membership. |
| `Workspace` | Tenant boundary separating cases, counterparty profiles, templates, and exports. |
| `Case` | Core claim aggregate tracking lifecycle, metadata, and pointers to templates/counterparties. |
| `EvidenceItem` | Evidence uploaded per case with hash, mime, source label, extraction status, and metadata. |
| `TimelineEvent` | Append-only events for status transitions, notes, uploads, and exports. |
| `MissingEvidenceCheck` | Rule evaluations stored with required/recommended flags, satisfaction booleans, and timestamps. |
| `ExportArtifact` | Deterministic bundle metadata (manifest hash, archive hash, storage key) for proof generation. |
| `CounterpartyProfile` | Lightweight merchant/landlord/carrier/manufacturer records sharable between cases. |
| `ClaimTemplate` | Planned templates describing required evidence sets for a theme or merchant vertical. |
| `AuditEvent` | Append-only audit spine with actor, action, entity, and metadata per mutation. |

## Future integrations
- **Liquefy** – a partner-grade packager/search service will plug into VaultPackager, supplying verified packing, search indexes, and proof artifact metadata without altering the public API.
- **NULLA** – workflow assistant that can observe readiness blockers, emit timeline events, and trigger evidence reminders via the existing router surface.
- **DNA anchoring** – paid exports will include cryptographic DNA anchors in the manifest so downstream consumers can verify the package's immutability.
