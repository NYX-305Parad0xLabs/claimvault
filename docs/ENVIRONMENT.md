# Environment configuration

ClaimVault relies on three `.env` files. Copy the matching `.env.example` files in the root, `apps/api/`, and `apps/web/` directories before running services. Key variables:

| File | Variable | Meaning |
| --- | --- | --- |
| `.env` | `DATABASE_URL` | SQLite connection used by the CLI and CLI-level checks. Defaults to `sqlite:///./claimvault.db`. |
| `.env` | `ENVIRONMENT` | Toggle between `development`, `staging`, and `production` to control logging/auto-migrations. |
| `.env` | `API_HOST`, `API_PORT` | Override the FastAPI `uvicorn` host/port. |
| `.env` | `SECRET_KEY`, `TOKEN_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Configure JWT signing. Keep secrets out of source control. |
| `.env` | `EXPORT_ROOT`, `NEXT_PUBLIC_API_BASE_URL`, `VAULT_PACKAGER` | Point exports to portable directories and choose between the default packager or future integrations (`default`, `liquefy`). |
| `apps/api/.env` | `DATABASE_URL` | Backend-only DB override used during `make api-*` commands. |
| `apps/api/.env` | `CLAIMVAULT_DATA_DIR` | Local data root for evidence/exports in dev environments. |
| `apps/web/.env` | `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_API_BASE_URL` | Base URL that the web UI uses to reach the FastAPI API. |

Do not commit `.env` files. Store sensitive values in your CI/CD secrets manager and point to them via environment variables when running services or GitHub Actions.
