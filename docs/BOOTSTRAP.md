# Bootstrapping

These steps turn a fresh ClaimVault clone into a working developer workspace.

1. Install Python 3.12+, Node 20+, and the pnpm CLI. Tools such as pyenv, the Windows Store, or your OS package manager are fine as long as the commands python, 
ode, and pnpm are on your PATH.
2. Copy the configuration templates into place before running any services (use the commands that match your shell):
   - Bash/zsh: cp .env.example .env, cp apps/api/.env.example apps/api/.env, cp apps/web/.env.example apps/web/.env
   - PowerShell: Copy-Item .env.example .env, Copy-Item apps/api/.env.example apps/api/.env, Copy-Item apps/web/.env.example apps/web/.env
3. Install dependencies with the shared bootstrap script or make install:
   - UNIX-like systems: scripts/bootstrap.sh
   - Windows PowerShell: scripts/bootstrap.ps1
   - Or run make install once to install both Python and JavaScript dependencies.
4. Validate the workspace with make ci, which runs Ruff, pytest, Alembic migrations, frontend lint/typecheck, and the scripts/check_imports.py guard so import-time side effects are caught early.
5. Start the services:
   - make api-dev
   - make web-dev

If you hit dependency conflicts, rerun the bootstrap script after cleaning 
ode_modules, .ruff_cache, or dist artifacts. Reference docs/DEV_SETUP.md for platform-specific troubleshooting and docs/GOVERNANCE.md to understand the required CI statuses and branch protection expectations.
