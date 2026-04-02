# Governance and Branch Protection

ClaimVault stays trustworthy by gating every merge through the full quality pipeline and an import-safety guard.

## Required Status Checks
- ackend-ruff
- ackend-pytest
- ackend-migrations
- import-check
- rontend-lint
- rontend-typecheck

Enable these statuses on GitHub for the main branch so merges cannot land until the backend lint/test/migration bundle, the import surface check, and the frontend lint/typecheck jobs pass. The import-check job runs scripts/check_imports.py to prove that importing pp does not trigger side effects, which keeps CI deterministic and prevents the suite from executing code outside request handlers.

## Branch Protection Recommendations
1. Protect main by requiring the above status checks and at least one approving review before merging.
2. Disallow direct pushes to main so work flows through feature branches (e.g., eat/whatever).
3. Enforce the checks to be up-to-date with the target branch so reruns capture the latest migrations and schema changes.
4. Tag large sweeps that touch both pps/api and pps/web so the reviewers can coordinate frontend/backend expectations (see docs/ARCHITECTURE.md and docs/ROADMAP.md).

Following these guardrails ensures every change is scanned for import-time effects, audited via the import-check job, and reviewed before the release engine runs.
