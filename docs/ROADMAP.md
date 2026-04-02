# Roadmap

## Near Term (Weeks 1–2)
1. **Harden REST payloads** with shared contracts and validation tests so the frontend can rely on stable types.
2. **Implement case timeline + missing-evidence rules** for return, dispute, and warranty claim types plus workflow transitions.
3. **Wire authentication + audit events** for every status change and evidence upload.
4. **Stabilize exports** (PDF/JSON) that capture timeline, evidence tags, and metadata.

## Mid Term (Weeks 3–6)
- Introduce **Alembic migrations** that mirror SQLModel schemas and ensure schema drift does not occur.
- Replace the development storage stub with a pluggable interface so uploads can later leverage S3 or similar.
- Add **audit dashboards** in the Next.js UI to surface compliance events and tamper alerts.
- Build **CI workflows** that lint/test Python, run ESLint/type checking in the frontend, and validate contracts.

## Longer Term (Month 2+)
- Keep all MVP features stable while exploring **automation hooks** for claim enrichment, review queues, and 3rd-party integrations.
- Expand exports into **compliance-ready packages** for partners (signed JSON, PDF, + manifest).
- Prepare the system for **secure onboarding** by adding RBAC layers and safer encryption for evidence-at-rest.


- Formalize the Liquefy vault seam by driving verified packing, searchable vault bundles, proof artifact streaming, and policy/redaction-aware exports through the new VaultPackager interface before the partner repo is onboarded.
- Layer in Liquefy safe-restore helpers and policy audits via the same seam once the integration surfaces APIs.
