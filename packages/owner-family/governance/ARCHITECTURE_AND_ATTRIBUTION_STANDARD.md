---
document_id: ARC-001
title: Architecture, data attribution and service boundaries
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to thoroughly document architecture and standardization; independent review pending
---

# Architecture, data attribution and service boundaries

## Applicability and authority

Applies to the owner-runtime family package, its supplied HTML KEX projections,
multiplexers, VFS, repository deployments and service boundaries. Technical
baseline issuance follows the owner's instruction; independent technical, legal
and certification review remains pending. The architecture set in `docs/architecture`
and source/package contracts support this standard. This is an internal standard,
not an assertion of ISO certification or worldwide invention.

## Mandatory architectural record

Every service MUST identify purpose, accountable owner, source and derivation,
execution location, interfaces, state, dependencies, resource limits, trust and
user boundaries, failure/recovery behavior, observable acceptance criteria and
known limitations. Every material decision MUST retain alternatives, rationale,
consequences and evidence. Use the architecture decision template; templates
remain Draft until an actual decision and authority are recorded.

## Data and file attribution

Originals MUST retain exact filenames and bytes in identified custody. Derived
sources and generated artifacts MUST have separate identities and hash-bound
provenance. Executable baselines MUST use complete commit IDs and qualified artifact
hashes. Credentials, private keys, customer data and mutable state MUST NOT enter
public release bundles. Record supplied authorship and third-party license metadata
without inventing a legal ownership conclusion.

Versioned data contracts MUST distinguish current records from historical source
claims. Breaking changes require migration, compatibility, test evidence and
rollback. Signed stateRoot/phaseRoot, actor returns and independent assessment
MUST retain their different meanings. Separate local observation roles MUST NOT
be represented as independent production assurance.

## User-space and service agreement boundaries

Each offered service MUST state its principal/user space, purpose, execution/data
location, access scope, recipient/transfer rules, retention, withdrawal, disconnect
semantics and acceptance version. Operational permission records MUST NOT be
presented as negotiated legal contracts. Owner tokens MUST NOT be issued through
public customer registration. Off-site services require configured host/scoped
credentials, transfer agreement and independently validated security controls.

Disconnect acknowledgement MUST identify its scope and what remains committed.
A family software admission fence MUST NOT be described as a host firewall,
physical disconnection or revocation of already dispatched effects.

## Claims and trajectory

Claims MUST distinguish implemented behavior, locally tested behavior, independently
assessed behavior and envisioned capability. Novelty/patentability requires a
separate prior-art and legal process. Physical power generation, large storage
capacity, multiple independent infrastructure planes and production SLAs require
measured evidence before assertion. Established primitives do not diminish real
integration work; integration evidence does not establish universal novelty.

## Review and change history

Review after material architecture, access, data transfer or claim changes, and at
least annually. Keep prior revisions in Git and controlled custody. The owner
maintains decisions; independent review and production promotion require separate
recorded authority and evidence.

- 1.0 — 7 October 2026: owner-directed architectural, attribution and service-boundary
  baseline issued; independent review pending.
