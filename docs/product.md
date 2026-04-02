# Product Notes

ClaimVault is the trust layer for Parad0x Labs customers who need a verifiable, auditable way to publish claims about their custody and compliance posture. Early customers expect:

- A deterministic ingestion path for claims that can be audited. The backend should provide typed endpoints and stored snapshots so auditors can verify what was submitted and when.
- Simple UI flows for operators to monitor claim health, confirm proofs, and make callouts for manual intervention when compliance gaps exist.
- Predictable deployments: the product should be runnable locally by clones of this repo and eventually by containerized infrastructure teams.

## Near-term Milestones
1. Finalize the claim schema in `packages/contracts` and build a FastAPI router that can ingest, store, and list claims.
2. Add Alembic migrations that capture core models (claim, issuer, verifier metadata) once approved.
3. Expand the Next.js UI to show claim trends, prove-of-reserve snapshots, and live status of back-office checks.
4. Introduce CI workflows for linting/formatting and tests, plus initial smoke tests for the API.

## Stakeholder Signals
- Emphasize auditability—every new feature should tie back to a requirement for traceable claims, logs, or approvals.
- Keep the experience low-friction—do not over-engineer the stack; the repo should remain navigable for small teams.
