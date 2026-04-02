# Domain Model

ClaimVault models revolve around verified evidence cases. Each entity feeds the proof bundle, readiness scoring, or audit spine.

## User
Operators and auditors that authenticate with JWTs. Users belong to workspaces via WorkspaceMembership and surface in audit/timeline events.

## Workspace & Membership
A workspace gates every case, counterparty profile, template, and export. Membership records tie users to a workspace with roles (owner, operator, iewer) so RBAC is scoped and deny-by-default.

## Case
The core aggregate. Each case supports five claim types (refund, warranty, chargeback preparation, shipment damage, rental deposit) and a lifecycle that tracks when the team is collecting evidence, needs more input, or is ready to export. Cases capture merchant/counterparty metadata, financials, dates, and references to CounterpartyProfile/ClaimTemplate when needed.

## EvidenceItem
Uploads tied to a case. Evidence items record kind, MIME type, SHA-256 hash, source label, extraction status (pending/completed/failed), and optional extracted text so audits can prove the bytes matched the manifest.

## TimelineEvent & AuditEvent
Both tables are append-only. Timeline events document manual notes, transitions, uploads, and exports. Audit events capture structured, immutable metadata about every mutation, including the actor, action, entity, and metadata JSON so reviewers can trace every decision.

## MissingEvidenceCheck
Every readiness rule evaluation writes a MissingEvidenceCheck entry so the system can show which rule was satisfied, which ones failed, and when the check ran.

## ExportArtifact
Deterministic export bundles (summary, case/timeline/evidence metadata, checksums) are tracked as ExportArtifact. Each row stores manifest/ archive hashes, metadata JSON, and the storage key so proofs can be validated later.

## CounterpartyProfile
Lightweight merchants, landlords, carriers, manufacturers, or marketplaces that provide reusable metadata per workspace. Each profile tracks an optional website, support email, support URL, and notes alongside the metadata JSON so the same counterparty can be referenced across claims without building a full CRM. Cases point to a profile via `counterparty_profile_id` but can still override `counterparty_name` when a title needs to differ from the canonical record.

## ClaimTemplate
Future-ready templates describe required evidence sets per workspace, letting readiness scoring and exports adapt to different lines of business.
