# Case Lifecycle

ClaimVault enforces a strict lifecycle so every status change is auditable, reasoned, and appended to the timeline.

| Status | Description |
| --- | --- |
| `draft` | Initial state. Case metadata can be edited freely and evidence is still being gathered. |
| `collecting_evidence` | Operators upload receipts, photos, and notes while the timeline records those activities. |
| `needs_user_input` | Missing-evidence rules flagged blockers; the workflow waits for more context before proceeding. |
| `ready_for_export` | Required evidence is satisfied and the case is primed for a deterministic export. |
| `exported` | Proof bundle (summary, case/timeline/evidence metadata, checksums, zipped files) has been generated. |
| `submitted` | The bundle left the system (bank, refunder, partner) and the case can still move to final states. |
| `resolved` | The outcome is settled, but the history remains open for audits. |
| `closed` | Final archival state; no further edits/transitions are permitted.

## Allowed transitions

- `draft → collecting_evidence`
- `collecting_evidence → needs_user_input`
- `collecting_evidence → ready_for_export`
- `needs_user_input → collecting_evidence`
- `ready_for_export → exported`
- `exported → submitted`
- `submitted → resolved`
- `submitted → closed`
- `resolved → closed`

Transitions must go through `CaseLifecycleService`; invalid jumps raise `InvalidCaseTransition` and HTTP 400 responses. Each transition records:

1. A **reason** (optional) that shows up in timeline metadata and audit events.
2. An append-only timeline event with `event_type="status_transition"`.
3. A matching audit entry so reviewers can trace who moved a case and why.
