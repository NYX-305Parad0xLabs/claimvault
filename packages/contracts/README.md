# Shared Contracts

This package holds the canonical JSON schemas for ClaimVault API surfaces. The FastAPI service loads these schemas for validation while the Next.js app can use them to render forms or documentation.

- `schemas/claim.json` - base schema for a claim payload + metadata.

### Usage
- Backend: load the JSON file (see `apps/api/app/api/v1/claims.py`) to keep error messages in sync with the schema.
- Frontend: consume the schema when building UDF editors or automated docs for `apps/web`.
