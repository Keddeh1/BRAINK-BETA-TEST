---
document_id: CTL-001
title: Controls, assurance and risk
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Controls, assurance and risk

## Control specification
Each control has a stable ID, objective, owner role, scope, implementation, frequency/trigger, evidence, operating status, test result, dependencies and remediation. Status is documented, partially implemented, implemented, verified operating or not applicable. Evidence links MUST support the claimed scope. Planned controls never appear as verified.

Not applicable requires an explicit scope-based rationale, owner decision and review date. Missing permissions, absent infrastructure or inconvenient work are blockers, not reasons to mark a relevant control not applicable. Local software validation and production validation may have different applicability.

## Risk and exception handling
Risk records contain cause/event/impact, assets, owner, likelihood and impact (1–5), inherent score, existing controls, residual score, treatment, due/review date and decision evidence. Scores aid triage; no numeric score substitutes for analysis. Unassessed values remain null.

Exceptions contain requirement/control ID, bounded scope, reason, impact, compensating controls, named approving authority, issued/expiry dates and remediation. Initial exception state is requested; no exception is approved by a placeholder or AI. Expired exceptions fail applicable release gates. Source-integrity mismatch, fabricated readbacks and same-generator independent assessment cannot be waived into a verified result; change requirements through governance if genuinely needed.

## Evidence quality and assurance
Separate observed result, source assertion, implementation claim and independent assessment. Retain command/exit status, target/environment, timestamps/timezone, actual bytes/readbacks, source/runtime/generation and digest/signature. Public evidence uses redacted derivatives linked to protected originals. Bundled evidence in uploads remains unverified until independently reproduced.

Review control performance quarterly and after incidents; corrective actions have an owner, acceptance evidence and closure review. Audit records retain exact inspected revision and limitations. Assessment independence cannot be inferred from two identities on the same key or from two containers on one host.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |
