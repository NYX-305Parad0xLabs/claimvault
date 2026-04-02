ï»¿# MVP Checklist

## Ready for release
- FastAPI app factory with structured logging, config, SQLModel, Alembic migrations, and import-guarded services.
- Authentication with JWTs, role-based workspace membership, and secure audit logging for key actions.
- Case CRUD, workflow transitions, readiness scoring, evidence uploads, timeline events, and deterministic proof exports.
- Next.js App Router UI with typed API client, case list/detail flows, audit visibility, readiness panels, and evidence support.
- Guardrails: shared .env templates, docs/BOOTSTRAP.md, docs/DEV_SETUP.md, docs/GOVERNANCE.md, scripts/check_imports.py, make ci, and GitHub Actions covering lint/test/migration/typecheck.

## Pending work (tracked via roadmap & issues)
- Email ingestion, OCR/text extraction, and merchant-specific templates for richer evidence capture.
- Case sharing workflows, Liquefy integration (packaging + search), and NULLA workflow assistant hooks.
- DNA-paid export delivery, S3/remote storage backend, Parad0x Command desktop companion, and mobile capture flow.
