---
document_id: CHG-001
title: Change and release control
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Change and release control

## Change classes
Standard: repeatable low-risk action under an approved runbook. Normal: reviewed material source, infrastructure, access or operational change. Emergency: urgent containment/recovery with bounded scope, named authority and retrospective review within two business days. Emergencies do not waive truthful evidence or secret custody.

Every material change records ID, owner, affected assets/environments, rationale, classification, dependency/impact analysis, exact source/revision, test evidence, risks, approval, execution window, rollback, operator and post-change readback. Routine engineering can proceed in a branch/draft; production execution waits for the relevant gates.

## Release gates
1. Exact source/archive custody and approved immutable build/image identity.
2. Required tests/builds completed; failures, skipped and unrun checks explicitly named.
3. Security/access and configuration review; externally provisioned credentials stay out of Git.
4. Environment capacity, network, service and recovery observations match target requirements.
5. Independent assessment is authenticated and distinct from generator for promotion.
6. Concrete transaction, authorization, rollback and agreed window recorded.
7. Post-change functional readback validates intended behaviour; unsuccessful change triggers rollback or incident handling.

A fixture success is development evidence. A renderer or listening PID is not deployment. Successful preflight is not host installation. A release manifest pins component commits, artifact hashes, evidence references and approval records. Record release outcomes as proposed, authorized, executing, verified, rolled-back or failed.

GitHub pull requests SHOULD be the review vehicle for material code/standard changes. Direct owner-authorized delivery is traceable through commit/change records; it MUST NOT be reported as peer reviewed. CODEOWNERS routes review but does not enforce it without platform protection. No rule requiring new approvals may retroactively cancel authorized development.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |
