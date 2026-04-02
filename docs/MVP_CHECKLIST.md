# MVP Checklist

## Core delivery (released)
- FastAPI factory with SQLModel, Alembic, structured logging, and dependency-injected services.
- JWT auth, role-based workspace membership, audit logging, and workspace-isolated imports.
- Case CRUD, strict workflow transitions, readiness scoring, evidence ingestion, timeline/notes, export bundling, audit surfaces, and manual extraction controls for captured proof text.
- Next.js App Router UI (login/register, case list/detail, readiness/audit panels, evidence upload/download) plus typed API clients.
- Guardrails: `.env` templates, `scripts/check_imports.py`, Makefile targets (`ci`, `import-check`, lint/test), and GitHub Actions running Ruff, pytest, migrations, lint, and typecheck.

## High-priority follow-up
- OCR/PDF/text extraction, email ingestion, and merchant-specific templates so readiness/export narratives stay consistent across claim types.
- NULLA/automation addition (missing-proof tasks, timeline summaries, evidence classification) without ever shipping synthetic AI claims.
- Liquefy and DNA/export upgrades, plus S3 storage, shareable handoffs, and mobile/desktop companions to make the platform enterprise-grade.
