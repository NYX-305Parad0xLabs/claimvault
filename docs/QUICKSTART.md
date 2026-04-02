# Quickstart

1. **Prepare your machine.** Install Python 3.12+, Node 20+, and a Unix-style shell (bash/pwsh) plus `make`. On Windows PowerShell, install Python/Node via the Microsoft Store or winget and use corepack to enable `pnpm`.
2. **Bootstrap dependencies.**
   - Copy the configuration templates: use `cp .env.example .env` (or `Copy-Item`/`Copy-Item apps/api/.env.example apps/api/.env` on PowerShell).
   - Run `make install` (or `scripts/bootstrap.sh` on macOS/Linux, `scripts/bootstrap.ps1` on Windows) to install the backend `claimvault-api` package and the frontend's pnpm workspace.
3. **Check the workspace.** Run `make ci` to exercise the import guard, Ruff, pytest, Alembic migrations, and the frontend lint/typecheck suites. The `ci` target is the single command that keeps the repo credible.
4. **Start services.** In one shell run `make api-dev`, and in another run `make web-dev`. Use the generated `.env` files to configure API URLs, secrets, and storage roots.
5. **Stay honest.** When you add new features, update `docs/ROADMAP.md` and the issue tracker so the public roadmap matches the code. Keep the `docs/ARCHITECTURE.md` and `docs/SECURITY_MODEL.md` aligned with any new services you wire into the FastAPI lifespan.
