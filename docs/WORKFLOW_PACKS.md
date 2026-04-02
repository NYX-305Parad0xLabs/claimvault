# Workflow packs v1

ClaimVault workflow packs give each claim type a semi-structured playbook: a narrative focus, readiness emphasis, and a curated set of tasks that keep operators honest. The first two packs — **Refund pack** and **Rental deposit pack** — land the product with clearly definable lanes while keeping the core engine flexible for future additions (warranty, shipment damage, chargeback prep).

## Why these two lanes?

- **Refund pack** covers the highest-volume operator scenario. Customers, merchants, and banks all care about the same proof points (order reference, receipt, merchant, and event timeline), so a narrow workflow allows quick wins and predictable exports.
- **Rental deposit pack** represents a complementary lane: longer timelines, photo-rich evidence, and communication logs. It stretches the platform toward landlord/tenant disputes with lightweight CRM-style context while sharing audit, export, and readiness infrastructure.

## What each pack provides

Each pack is described in code (`app.workflow.packs`) and exposed via the summary preview endpoint:

- **Name & summary**: shown at the top of every preview and export so reviewers know which pack guided the work.  
- **Export focus**: influences the summary language inserted into `summary.md`.  
- **Preset tasks**: derived from readiness rules and surfaced both in the UI and the summary preview. Tasks auto-mark as `open` when their rule is missing and `complete` once satisfied.

### Refund pack
- **Focus**: Purchase context, merchant clarity, proof of return, and timeline narrative.  
- **Tasks**:
  - Capture the order reference.
  - Record the merchant name.
  - Upload a receipt or order document.
  - Log at least one timeline entry.

### Rental deposit pack
- **Focus**: Tenancy window, condition inspections, landlord communication, and photo evidence of damages/disputes.  
- **Tasks**:
  - Log move-in/out inspections.
  - Add condition or damage photos.
  - Summarize landlord communications.

## What’s next

Future packs (warranty, shipment damage, chargeback prep) plug into the same structures: add a `WorkflowPack` definition, tune readiness rules, and optionally provide presets or export verbiage. The workflows remain deterministic, audited, and export-ready, so later packs can be rolled out without re-educating the engine.
