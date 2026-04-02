# Architecture Overview

ClaimVault starts as a monorepo with a FastAPI backend, a Next.js frontend, and a shared schema contract package. The key principles guiding this first iteration are:

- **Contract-first design:** `packages/contracts` stores JSON schemas that describe every API surface. FastAPI uses the contract to validate payloads, and the Next.js UI can introspect the contracts for forms or documentation later.
- **Lean backend stack:** The FastAPI app lives inside `apps/api`. SQLModel builds the declarative schema, Alembic provides migration scaffolding (even if empty for now), and SQLite keeps local development simple.
- **App Router frontend:** `apps/web` leverages Next.js 15 App Router to host product pages, status dashboards, and eventually secure connective experiences.
- **Workspace tooling:** `pnpm-workspace.yaml` keeps the Next.js app manageable while the root Makefile, `.env.example`, and scripts/ directory accelerate onboarding and scripting tasks.

## Data Flow
1. The frontend will POST validation requests to `/api/claims` (FastAPI router) using the contract-defined shape.
2. FastAPI endpoints parse the contract, persist via SQLModel, and return typed responses for the UI to render.
3. Contracts evolve inside `packages/contracts` so both backend and frontend stay in sync.

## Vault Packaging Seam
- The export service now delegates bundle creation to a `VaultPackager` interface. The `DefaultVaultPackager` zips case metadata, timeline, and evidence with deterministic entries, while a `LiquefyPackager` stub holds placeholder adapters for the future partner integration. A runtime switch (env `VAULT_PACKAGER=liquefy`) will flip which implementation FastAPI instantiates, keeping the API surface stable even as external vendors change.
- Because the packager seam isolates file formatting, adding Liquefy's verified packing, search, proof artifact extraction, policy/redaction controls, or safe restore helpers will not require touching case services or timeline logic—the integration will only implement the new `VaultPackager` contract.

## Operational Notes
- Local runs rely on `.env` values (see `.env.example`). There is no production infrastructure yet.
- Use the Makefile for linting, installing, and running the apps as shown in the README.
- Logs and migration scripts will be added once the first claim workflow stabilizes.
