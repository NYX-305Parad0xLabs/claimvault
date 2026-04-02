# ClaimVault

ClaimVault is the case-building and export engine Parad0x Labs uses to turn returns, disputes, chargebacks, and warranty investigations into auditable proof bundles. The platform combines a typed FastAPI backend, a responsive Next.js UI, and shared contract definitions so every mutation stays observable, validated, and traceable.

## Vision
- Provide operators with a trustworthy timeline and missing-evidence checklist before any claim leaves the org.
- Keep MVP infrastructure lean (FastAPI + SQLite + Next.js) so the team can iterate without heavy ops costs.
- Preserve trust through append-only audit events, deterministic exports, and transparent readiness rules.

## Current MVP Scope
1. FastAPI backend with SQLModel + Alembic, auth/RBAC, readiness analysis, audit spine, evidence storage, and proof exports.
2. Next.js 15 App Router frontend with typed API client, login/register flows, case listings, detail timelines, readiness panels, and audit visibility.
3. Shared JSON schemas in packages/contracts to keep backend and frontend contracts aligned.
4. Guardrails for local development: .env templates, import-check scripts, Makefile helpers, and CI workflows.

## Stack
| Layer | Tooling |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLModel, Alembic, Ruff, Pytest, SQLite |
| Frontend | Next.js 15, React 18, TypeScript, ESLint, pnpm |
| Contracts | packages/contracts JSON schemas consumed by API routes and the typed client |
| Tooling | Makefile, scripts/bootstrap, scripts/check_imports, GitHub Actions CI |

## Quickstart
1. Clone the repo and jump into it: git clone git@github.com:<you>/claimvault.git && cd claimvault.
2. Copy the shared configuration samples and adjust secrets:
   - cp .env.example .env
   - cp apps/api/.env.example apps/api/.env
   - cp apps/web/.env.example apps/web/.env
3. Install dependencies via the shared scripts: make install (or run scripts/bootstrap.sh on UNIX, scripts/bootstrap.ps1 in PowerShell).
4. Ensure quality gates pass locally with make ci (runs Ruff, pytest, migrations, frontend lint/typecheck, and the import guard).
5. Start the services:
   - make api-dev
   - make web-dev
6. Reference docs/BOOTSTRAP.md for the onboarding checklist, docs/DEV_SETUP.md for OS-specific tips, and docs/GOVERNANCE.md for branch protection requirements.

## Repository Layout
- pps/api â€“ FastAPI service with routers, models, services, migrations, tests, and runtime guardrails.
- pps/web â€“ Next.js App Router frontend, typed API client, and the UX for cases, evidence, and audits.
- packages/contracts â€“ Shared JSON schemas for API payloads, responses, and exports.
- docs/ â€“ Product, architecture, roadmap, security, bootstrap, and governance guidance.
- scripts/ â€“ check_imports.py, platform bootstrap helpers, and future automation hooks.
- Root files â€“ Makefile targets, .env.example, .editorconfig, .gitattributes, and the MIT license.

## Tooling
- make install â€“ installs backend and frontend dependencies.
- make api-dev / make web-dev â€“ launch the FastAPI and Next.js services.
- make api-test, make api-lint, make api-migration â€“ backend quality gates.
- make web-lint, make web-typecheck â€“ frontend validation.
- make import-check â€“ detects import-time side effects that could break CI.
- make ci â€“ runs all the above so CI status checks stay green.

## Docs & Governance
- docs/ARCHITECTURE.md â€“ system context, entity list, API surface, and the VaultPackager seam ready for Liquefy.
- docs/ROADMAP.md â€“ planned milestones from foundation to proof exports and partner integrations.
- docs/SECURITY_MODEL.md â€“ assumptions, controls, audit spine, and threat lists for evidence/case integrity.
- docs/BOOTSTRAP.md + docs/DEV_SETUP.md â€“ onboarding and platform-specific dev tips.
- docs/GOVERNANCE.md â€“ recommended GitHub Actions statuses and branch protection rules.

## Continuous Integration
GitHub Actions enforces the following checks on main and pull requests:
- ackend-ruff
- ackend-pytest
- ackend-migrations
- import-check
- rontend-lint
- rontend-typecheck

Protect main with these statuses plus required reviews so the audit trails stay trustworthy.

## Next Steps
1. Expand the shared contracts to cover additional claim payloads and proof artifacts.
2. Automate Liquefy packing, search, and redaction through the VaultPackager seam.
3. Add end-to-end tests to lock down the case lifecycle across the API and web UI.
