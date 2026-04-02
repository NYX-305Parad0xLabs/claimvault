# Case Lifecycle

ClaimVault tracks every claim through a guarded lifecycle so teams know exactly what actions are safe.

| Status | Description |
| --- | --- |
| draft | Initial state right after creation. The case can be edited freely and the timeline is empty. |
| collecting_evidence | Operators gather receipts, photos, notes, and timeline entries. Evidence uploads and notes append events here. |
| 
eeds_user_input | Readiness rules flagged missing proof. Workflow stays in this state until the operators upload the missing artifacts. |
| eady_for_export | Required evidence is satisfied, score is high, and the case can be exported. |
| exported | A deterministic bundle (summary.md, case.json, 	imeline.json, evidence_manifest.json, checksums.txt, zipped evidence) has been produced and recorded as an ExportArtifact. |
| submitted | The proof package left the system (e.g., submitted to a bank, refunder, or partner). |
| esolved | The dispute/refund outcome is settled but marketing or legal may still inspect the history. |
| closed | Final archival state. No further edits or exports happen after closing. |

Transitions are enforced via CaseService.transition_case and appended to the timeline and audit spine. Invalid jumps (e.g., draft → eady_for_export) raise errors so the history is deterministic.
