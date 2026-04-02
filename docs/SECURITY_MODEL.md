# Security Model

## Assumptions
- Operators and auditors authenticate before accessing the UI or API; token/session secrets are rotated per release.
- The development environment targets local SQLite and filesystem storage; production will deploy hardened storage and a managed database.
- Uploaded evidence is treated as sensitive data and must not be executed or rendered outside sanitized viewers.
- The FastAPI service never executes user-provided code at import time; all processing is triggered through request handlers with dependency-injected contexts.
- Audit log entries are append-only and immutable once written; downstream systems may replicate them but cannot alter historical records.

## Controls
| Control | Description |
| --- | --- |
| Authentication | FastAPI endpoints require bearer tokens or session cookies; Next.js obtains a CSRF-protected token before interacting with write paths. |
| Audit logging | Every status change, file upload, evidence tag, timeline event, and export action writes an audit record capturing actor, timestamp, action, and claim identifier. |
| Evidence storage | Uploaded files are written via the storage interface; the default local implementation uses directories with randomized filenames and content scans before tagging. |
| Dependency injection | Services are provisioned at app startup and injected through `Depends`, avoiding global mutable state that attackers might manipulate. |
| Export integrity | Proof bundles include digital fingerprints (hashes) of each evidence file, enabling later verification that exports have not been tampered with. |

## Authentication & Authorization

- **Password safety:** Operator credentials are hashed with bcrypt via `passlib` and only the hash is persisted; duplicate emails are rejected to avoid enumeration.
- **Token-based access:** JWT access tokens are signed with the environment-provided `SECRET_KEY`, expire in under 60 minutes, and embed workspace identifiers plus role claims.
- **Workspace RBAC:** Every case-interacting request resolves the user’s workspace membership. Owner/operator roles unlock write paths, while viewer access is deny-by-default, so protected endpoints return 403 when roles are insufficient.
- **Audit trails:** Registrations and logins append audit events recording actor, workspace, and action metadata; once written, these records remain immutable.

## Threat Models
### Threats to Uploaded Evidence
- **Tampering in transit:** An attacker intercepts uploads and modifies receipts or screenshots before they are stored. *Mitigation:* TLS for all client calls + server-side content checksums before persisting.
- **Malicious uploads:** Uploaded files contain embedded scripts or exploits. *Mitigation:* Files are treated as data blobs, never executed, and stored outside of the static assets root. Antivirus/scanning will run in later iterations.
- **Storage enumeration:** A compromised operator tries to access other evidence files directly. *Mitigation:* The storage interface enforces claim-bound references; each file reference is scoped to its originating claim and an audit record tracks access.

### Threats to Case Integrity
- **Status rollback:** Unauthorized rollback of a status step to hide escalation. *Mitigation:* Status transitions are append-only timeline events; the API rejects back-dating transitions if they conflict with audit order.
- **Missing evidence suppression:** An attacker clears missing-evidence flags to falsely mark a case complete. *Mitigation:* Missing rules are codified in configurable rule sets stored with each claim type and recalculated on every detail fetch.
- **API contract drift:** Frontend or third parties call endpoints with malformed payloads to insert inconsistent data. *Mitigation:* Shared JSON schemas validate payloads server-side; Pydantic models reject invalid structures before persistence.
- **Export tampering:** Someone replaces files in the export bundle after generation. *Mitigation:* Each bundle includes a manifest with evidence hashes and audit summaries, making tampering detectable.
