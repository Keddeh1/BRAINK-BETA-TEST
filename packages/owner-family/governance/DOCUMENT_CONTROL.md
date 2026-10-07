---
document_id: DOC-001
title: Controlled documents and records
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Controlled documents and records

## Identification and required metadata
Every controlled policy, standard or procedure MUST have a stable document ID, title, revision, status, classification, accountable owner, issue date, next review date, approval basis, applicability and change history. The machine-readable document register adds path, SHA-256 and review/approval state. IDs are never reused. Working notes and external uploads are records, not automatically controlled standards.

Classification: Public, Internal, Confidential or Restricted. Credentials/private keys and sensitive operational evidence MUST NOT enter public repositories. Public baseline standards carry no secret values. Originals in private repositories retain their original names and exact bytes.

## Lifecycle
Draft → In review → Approved → Issued → Superseded → Archived. Rejected and Withdrawn are explicit terminal decisions. Initial owner-authorized baseline issuance is recorded separately from independent technical review, which remains pending. Future material revisions MUST record their reviewer and approval evidence before claiming approval. Drafts can be developed without waiting for production inputs.

A material requirement change increments the major revision; clarifications increment the minor revision. Preserve the prior version through Git history plus the release manifest. Git timestamps alone are not approvals. Record approval identity, decision, timestamp/timezone, exact revision/hash and reference. Never silently alter issued content: update revision/change history and register hash.

## Review and distribution
Review at least annually, with quarterly governance oversight; also review after incidents, architectural/access changes or changed obligations. A missed review flags an overdue document without silently retiring it. The canonical baseline is the runtime repository governance directory. Queue and other repository copies MUST identify the canonical commit and document hashes; local copies are uncontrolled unless checked against that revision.

## Record custody and retention
Keep source originals immutable in custody; derived artifacts receive distinct identities. Evidence MUST bind source/runtime/generation, command, timestamps, outcome, hashes and assessor where applicable. Never overwrite a negative result with a passing narrative.

Interim operational retention: policy versions and approval/change/release/incident/evidence records for seven years after supersession or closure; routine diagnostic logs for 90 days; source custody retained for the supported component lifetime plus seven years. This is an internal default, not a legal mandate. Owner validates obligations and adjusts retention through a controlled change. Legal/contractual holds override deletion. Default periods authorize retention, not automatic deletion; destruction requires a recorded authorization and verified recovery/hold check.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |
