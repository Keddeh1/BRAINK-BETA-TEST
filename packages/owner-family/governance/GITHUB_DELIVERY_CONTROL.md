---
document_id: GIT-001
title: Repository delivery and tracking
revision: 1.1
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Repository delivery and tracking

## Tracking
Use existing milestones M1–M4 and issue track/area/type/priority/evidence/blocker labels. Keep development implementation status separate from production-validation status; blocked external inputs do not suspend unrelated local engineering. Link concrete commits/PRs, acceptance readbacks and dependencies. Close only satisfied issue scope.

The private deployment queue retains originals and protected records. The public runtime repository is the canonical governance baseline and public engineering evidence. Classification governs record placement. Do not copy private source contents into public policy mirrors.

## Review and automated validation
Use .github/pull_request_template.md and governance/templates. Governance document metadata, register consistency and SHA-256 are checked by scripts/check_governance.py. The governance workflow requests this check on pushes and pull requests. A workflow definition is not proof that GitHub executed it successfully; inspect run evidence. The local check does not validate human approvals or production controls.

CODEOWNERS names @Keddeh1 as accountable review routing. Branch protection/rulesets, required checks and independent review are not verified or enforced by that file. The integration currently denies reading main branch protection; treat protection state as unknown. Do not claim it is absent or enabled.

Project creation is denied by integration scope. Six designed views remain documented; active milestones, labels, issues and filtered lists are available. Enable actual Project fields/views when authorized access exists; this restriction does not apply to repository delivery.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |

## First hosted execution evidence

GitHub run 37570148724 completed with failure before any job steps executed. Check-run annotation: "The job was not started because your account is locked due to a billing issue." Hosted execution is blocked; the local integrity check passed and rejected a deliberately altered document. This is not a validator failure and does not restrict pushes/issues. Resume hosted validation after the billing lock is resolved; do not claim a passing or required check until observed.

| 1.1 | 2026-10-07 | Record actual hosted-run billing denial and local verification scope | Owner-authorized governance implementation; independent review pending |
