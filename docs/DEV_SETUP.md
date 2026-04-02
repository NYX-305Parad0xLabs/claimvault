# Development setup & guardrails

Follow [docs/QUICKSTART.md](QUICKSTART.md) for the canonical onboarding steps (copy env templates, run the bootstrap scripts, exercise `make ci`, then start `make api-dev`/`make web-dev`).

## Operating-system notes
- **Windows:** run `scripts/bootstrap.ps1` from PowerShell, copy root/API/web `.env.example` files with `Copy-Item`, and keep `corepack enable pnpm` on your PATH.
- **macOS/Linux:** use `scripts/bootstrap.sh`, copy the `.env.example` templates with `cp`, and enable `pnpm` through `corepack` or `npm install -g pnpm`.
- **Make targets:** `make install` bootstraps both Python and pnpm dependencies. Use `make ci` to run ruff, pytest, migration smoke tests, the import guard, and both frontend lint/typecheck pipelines.

## Testing & guardrails
- `apps/api/tests/conftest.py` configures SQLite-backed fixtures so each pytest run spins up a temporary file; the repo never touches production data.
- `scripts/check_imports.py` loads every module under `app` to catch import-side effects before the server starts. The `import-check` Make target and CI job run this guard automatically.
- Keep `.env` files private. Use `docs/ENVIRONMENT.md` for reference values, and let environment variables (GitHub Secrets, .env files stored locally) hold credentials.
