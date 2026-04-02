# ClaimVault API

This FastAPI application exposes the claim ingestion and listing endpoints for ClaimVault. It relies on SQLModel for schema definitions, Alembic for migrations, and loads shared claim contracts from `packages/contracts`.

## Running locally
1. Copy `.env.example` to `.env` and adjust `DATABASE_URL` if necessary.
2. `python -m pip install -e .` to install the service in editable mode.
3. `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` to start the API.

## Linting & Tests
- `ruff check app`
- `pytest`

## Future work
- Add Alembic migrations under `apps/api/alembic` once the first models stabilize.
- Expand tests to cover contract validation and persistence.
