# Non-Goals

ClaimVault MVP focuses narrowly on verified evidence cases, not broad platform features. The following are intentionally out of scope for this release:

- Live email or SMS ingestion pipelines (email/WhatsApp) that auto-create cases.
- Payment processing or refund issuance; ClaimVault documents the case, it does not move money.
- Liquefy search/packing, NULLA automation, DNA anchoring, or any external partner integrations—they are planned for phased upgrades.
- Browser extensions, mobile apps, or Parad0x Command desktop companions; the MVP ships a Next.js App Router web experience only.
- Multitenant or hosted storage besides the local SQLite/filesystem defaults (S3/backups come later when needed).
