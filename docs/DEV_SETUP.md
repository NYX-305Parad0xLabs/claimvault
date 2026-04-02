# Development Setup

## Prerequisites
- Python 3.12+ with pip3 on your PATH.
- Node 20+ with npm, and the pnpm CLI (corepack enable pnpm or install it globally).
- GNU make (or another make implementation) so the shared targets (make ci, make api-test, etc.) can run reliably.

## Windows
1. Use the Microsoft Store, winget, or the official installers to put Python 3.12, Node 20, and pnpm on your PATH.
2. Copy the env templates (root, API, and web) before starting services:
   - Copy-Item .env.example .env
   - Copy-Item apps/api/.env.example apps/api/.env
   - Copy-Item apps/web/.env.example apps/web/.env
3. Run scripts/bootstrap.ps1 or make install to install the backend claimvault-api package plus the frontend dependencies.
4. Run make import-check to prove there are no import-time side effects and make ci to run the full suite.
5. Start the services with make api-dev and make web-dev.

## macOS / Linux
1. Use Homebrew, apt, dnf, or your distro package manager to install Python 3.12+ and Node 20.
2. Enable pnpm via corepack enable pnpm or 
pm install -g pnpm.
3. Copy the env templates (same as above) before running any commands.
4. Bootstrap the workspace with scripts/bootstrap.sh or make install.
5. Validate the workspace with make ci and use make api-dev / make web-dev to run services.

## Testing & Guardrails
- Backend tests (make api-test) run against temporary SQLite files configured in pps/api/tests/conftest.py, so each run uses an isolated data directory and does not touch production artifacts.
- scripts/check_imports.py discovers import-time side effects; include it in your pre-flight checks (make import-check or the import-check GitHub Actions job).
- Keep .env files out of source control; use the provided .env.example templates as a starting point and store secrets in the environment or a credential manager.
- The claimvault package wires services during the FastAPI lifespan so there are no import-time side effects and all shared resources (engine, storage, packagers) live in pp.state.

Refer to docs/BOOTSTRAP.md for a condensed checklist and docs/GOVERNANCE.md for the required CI statuses before merging into main.
