# ClaimVault

ClaimVault is the custody-first infrastructure layer that Parad0x Labs needs to deliver frictionless, compliance-aware proof-of-reserve and credential management services. The repo captures the early MVP: a verified-claim ingestion API plus a responsive marketing/operations web interface.

## Vision
- Secure every customer claim lifecycle with typed contracts, schema-driven validation, and audit-friendly logging.
- Deliver a lightweight, SQLite-powered development backend that can later grow into full-scale accounts via zero-trust onboarding flows.
- Surface health, usage, and confidence signals through a polished Next.js experience no matter the screen size.

## Current MVP Scope
1. FastAPI backend with SQLModel models, Alembic wiring, and contract-aware endpoints for claim issuance + verification.
2. Next.js App Router frontend that showcases product positioning, customer journey, and API observability hooks.
3. Shared JSON schema library in `packages/contracts` so backend and frontend speak the same language.
4. Developer tooling (Makefile, scripts/bootstrap, `.env.example`, CI-friendly layout) to jumpstart product iterations.

## Stack
| Layer | Tooling |
| --- | --- |
| Backend | Python 3.12, FastAPI, SQLModel, Alembic, SQLite, Ruff, Pytest |
| Frontend | Next.js 15, TypeScript, ESLint |
| Workspace | pnpm workspace, shared contracts folder |
| Tooling | Makefile entry points, docs for architecture, scripts for bootstrap |

## Repository Layout
- `apps/api` – FastAPI service, SQLModel schema, contract-aware routes, and testable entrypoints for local/CI workloads.
- `apps/web` – Next.js 15 App Router presentation layer, ready for marketing + internal dashboards.
- `packages/contracts` – JSON schema + typed API contract source of truth shared between services.
- `docs/` – Architecture thinking, product hooks, and context for contributors.
- `scripts/` – Developer helpers for bootstrapping workloads (virtualenv, pnpm install, etc.).
- Root config – MIT license, Makefile tasks, `.editorconfig`, `.gitattributes`, `.env.example`, and CI-ready structure.

## Getting Started
1. Copy `.env.example` to `.env` and adjust `DATABASE_URL` if you need a different location.
2. `make install` to bootstrap Python deps and install pnpm packages.
3. `make run-backend` and `make dev-web` in separate terminals to start the FastAPI API and Next.js frontend.
4. Refer to `docs/` for architecture rationale before adding new services or data flows.

## Next Steps
- Wire up Alembic migrations and CI workflows once the first data model is captured.
- Add end-to-end tests that exercise both the REST contract and the Next.js UI content.
- Iterate on the shared schema package to cover multiple claim types (verifiable credentials, proof of reserves, etc.).
