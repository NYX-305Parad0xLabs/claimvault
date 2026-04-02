# ClaimVault API

This FastAPI application exposes the case ingestion, workflow, and authentication endpoints for ClaimVault. It relies on SQLModel for schema definitions, Alembic for migrations, JWT tokens for authentication, and loads shared claim contracts from `packages/contracts`.

## Authentication

- `POST /api/auth/register`: create an operator account, workspace, and owner membership.
- `POST /api/auth/login`: exchange credentials for a JWT Bearer token that encodes the workspace and role.
- `GET /api/auth/me`: inspect the current operator and workspace membership using the active token.

Protected routes require the `Authorization: Bearer <token>` header. The test secret and token lifetime are configured via `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and `TOKEN_ALGORITHM`.

## Case Timeline & Notes

- `GET /api/cases/{id}/timeline`: fetch the append-only timeline ordered by `happened_at`.
- `POST /api/cases/{id}/timeline-events`: append manual events (status checks, audits, or evidence links); owner/operator roles only.
- `POST /api/cases/{id}/notes`: add or correct user-created note entries (immutable history, corrections tracked via `corrects_event_id` metadata).
- Timeline entries can reference evidence (optional `evidence_id`) and each write generates a matching audit record.
- `GET /api/cases/{id}/readiness`: run the lightweight rules engine to surface missing evidence, recommended artifacts, and blockers before exporting a case.

## Running locally
1. Copy `.env.example` to `.env` and adjust values (especially `SECRET_KEY` and `DATABASE_URL`).
2. `python -m pip install -e .[dev]` to install the API and dev dependencies in editable mode.
3. `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` to start the API.

## Linting & Tests
- `ruff check .`
- `pytest`

## Future work
- Expand Alembic migrations under `apps/api/alembic` once models finalize.
- Grow the API surface (case transitions, evidence upload, exports) with additional integration tests.
