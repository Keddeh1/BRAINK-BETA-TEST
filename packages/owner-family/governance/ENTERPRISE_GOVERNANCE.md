---
document_id: GOV-001
title: Enterprise governance and accountability
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Enterprise governance and accountability

## Scope and authority
This baseline governs KEDDEH namespace runtime engineering, uploaded component custody, the deployment queue, operational releases and their supporting records. It is issued under the repository owner's instruction to establish enterprise governance. Issuance is not independent assurance, certification or evidence that every control operates. Repository access does not confer production infrastructure access.

Normative terms: MUST is mandatory; SHOULD permits a documented justified exception; MAY is optional. Current application behaviour takes precedence over unsupported assertions in research material. Controlled exceptions cannot falsify acceptance evidence.

## Accountability and separation
| Role | Accountability | Appointment |
|---|---|---|
| Accountable owner | Scope, policy adoption, risk acceptance, access ownership, appointments | Keddeh1, repository owner |
| Document custodian | Register, revisions, review routing, supersession, access and retention | Unassigned; owner accountable until delegated |
| Engineering implementer | Design, source provenance, tests, remediation and proposed changes | Recorded per change; automation may prepare artifacts |
| Technical reviewer | Review design, diff and test evidence | Unassigned per change; no review is inferred from merge |
| Release/change authority | Approve concrete production transaction and rollback | Owner or explicitly appointed delegate |
| Independent assessor | Separate key/identity and independent assessment of promotion evidence | Unassigned; generator cannot self-assess |
| Operator | Execute approved transaction; retain readbacks and incident records | Unassigned per environment |

One person may hold several development roles, but a production generator MUST NOT supply their own independent assessment. If independent personnel are unavailable, retain the promotion blocker rather than inventing independence. AI output is preparatory work, not an accountable human approval.

## Decision rights
Routine reversible development, local checks, document maintenance and repository delivery within the owner's instructions can proceed. Production release, DNS/registrar changes, privileged access changes and destruction require a concrete change record and the applicable authority. Avoid requesting renewed permission for previously authorized routine work.

Owner reviews governance and exceptions quarterly, after material incidents and on substantial architecture changes. Unassigned roles and overdue controls appear in registers, not hidden in prose. Track A hosted web delivery and Track B sovereign runtime retain separate readiness decisions.

## Reference frameworks
Use ISO 9001 documented-information principles, ISO/IEC 27001 information-security management concepts, NIST CSF 2.0 governance outcomes and NIST SP 800-53 control-family concepts as design references. No certification, complete framework mapping or compliance attestation is asserted. Contractual, legal and sector obligations require a separately identified obligations register and competent review.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |
