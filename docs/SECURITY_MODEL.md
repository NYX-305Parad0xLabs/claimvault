# Security Model

## Assumptions
- Only authenticated operators and auditors may interact with the UI or API; secrets (JWT signing keys, bcrypt salts) rotate as part of each release cadence.
- FastAPI uses dependency injection so no code runs at import time; lifecycle wiring happens through the create_app factory and pp.state.
- Local dev runs on SQLite and filesystem storage; production will replace these with durable databases and object stores while keeping the same contract surface.
- Evidence files are treated as data blobs, never executed, and stored under the workspace-and-case-scoped CLAIMVAULT_DATA_DIR to avoid static asset exposure.
- Every workflow mutation writes an append-only audit event so downstream reviewers can inspect the provenance of changes.

## Controls
| Control | Description |
| --- | --- |
| Authentication | JWT tokens signed with SECRET_KEY, with the token lifetime governed by ACCESS_TOKEN_EXPIRE_MINUTES. Passwords are hashed with bcrypt before persisting. |
| Workspace RBAC | Users belong to workspaces with roles (owner, operator, iewer). All protected routes perform deny-by-default role checks via the current_user/
equire_workspace_membership dependencies. |
| Evidence storage | The storage interface keeps uploads within the evidence root, uses SHA-256 digests, and never trusts client-provided filenames; metadata is recorded alongside audit events. |
| Audit spine | Every sensitive operation (case lifecycle change, evidence upload, export generation, login/registration) writes an AuditEvent. The /cases/{id}/audit-events API surfaces human-readable summaries for the UI, enforcing workspace scoping. |
| Import-time guard | scripts/check_imports.py is part of the import-check job (and make import-check) to ensure the API package loads cleanly without unexpected side effects before CI runs. |
| Testing hygiene | Pytest fixtures (see pps/api/tests/conftest.py) point the database and storage paths to temporary directories so tests are isolated from production data. |

## Audit Spine
The append-only audit stream captures entity_type, entity_id, ction, ctor, and contextual metadata for every case mutation, evidence operation, and export. The API orders events by happened_at and filters by workspace so viewers cannot see unrelated audit entries. The case detail UI renders the spine with human-friendly labels (e.g., status: draft â†’ collecting_evidence, evidence uploaded from browser, March export bundle generated). Liquefy or other automation hooks must log through the same spine to retain a single trust surface.

## Authentication & Authorization
- **Password safety:** Operator credentials are hashed with bcrypt; duplicate emails and weak passwords are rejected during registration.
- **Token-based access:** JWTs embed workspace IDs and role claims, expire in under an hour, and are signed with SECRET_KEY + TOKEN_ALGORITHM.
- **Workspace RBAC:** Protected endpoints enforce membership checks. Viewer roles can read but cannot mutate case data or evidence; owners/operators gain elevated permissions. Authorization failures return 403 with an audit event that notes the actor, workspace, and attempted action.
- **Audit trails for auth:** Login, logout, and registration append AuditEvent entries so the operations are traceable in the case detail audit tab.

## Operational Guardrails
1. **Import guard:** make import-check runs scripts/check_imports.py to confirm pp modules import cleanly. The GitHub Actions import-check job enforces the same guard on every PR.
2. **Makefile targets:** make ci bundles Ruff, pytest, migrations, and frontend lint/typecheck so the entire stack is validated before merging. Running make ci locally mirrors the required status checks.
3. **Environment templates:** Root and app-level .env.example files document the minimum settings and prevent secrets from leaking into source control.
4. **Deterministic exports:** The VaultPackager interface produces deterministic bundles (summary.md, case.json, 	imeline.json, evidence_manifest.json, checksums.txt) so auditors can verify bytes without guessing.
5. **Append-only timeline:** Timeline events are append-only; corrections append follow-up entries rather than rewriting history, and each change writes an AuditEvent.

## Threat Models
### Threats to Uploaded Evidence
- **Tampering in transit:** Attackers modify receipts before storage. *Mitigation:* TLS, server-side SHA-256 hashing, and storage keys scoped by workspace/case.
- **Malicious uploads:** Files contain scripts or executables. *Mitigation:* Files are treated as data blobs, stored outside static roots, and validated by mime sniffing + size limits. Future scans can plug into the storage interface.
- **Storage enumeration:** An operator tries to download evidence from another workspace. *Mitigation:* Download routes enforce workspace membership and record the access in an AuditEvent.

### Threats to Case Integrity
- **Status rollback:** Unauthorized status changes hide escalation history. *Mitigation:* Transition rules only allow forward steps; invalid transitions return 400 and log rejections.
- **Missing evidence suppression:** Attackers try to mark incomplete cases ready. *Mitigation:* Readiness rules run on every detail fetch and document missing/optional items; export readiness includes blockers reported alongside the score.
- **API contract drift:** Malformed payloads slip through and corrupt state. *Mitigation:* Shared JSON schemas live in packages/contracts; FastAPI routes validate payloads before persistence and return structured errors.
- **Audit tampering:** Someone edits audit history. *Mitigation:* Audit entries are append-only (no update/delete), scoped by workspace, and surfaced in the UI so reviewers can detect missing records.
