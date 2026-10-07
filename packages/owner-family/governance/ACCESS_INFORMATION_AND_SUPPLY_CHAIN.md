---
document_id: SEC-001
title: Access, information and supply-chain control
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Access, information and supply-chain control

## Access
Maintain an access register for repository, Projects, Drive, DNS, registrar, registry, servers and archive storage. Record principal, role, resource, granted capabilities, approval reference, expiry/review and last verified operation; never credential values. Least privilege and quarterly review apply. Review revocation on role departure and incidents.

GitHub code/issues permissions do not imply Projects administration or branch-protection administration. Confirm the specific capability through its actual operation. Do not request personal tokens when injected authentication already works. Private artifacts stay in private repositories; classification changes require owner-authorized disclosure review.

## Secrets and trust
Private signing/TSIG keys, bearer tokens and recovery credentials use an owner-controlled secure secret store or authorized delivery channel, outside Git, issue bodies and shell arguments. Document rotation, revocation, checkpoint/trust distribution and recovery. Registry tokens are minimum 32 characters; trust policy restricts signing identities by role and runtime. Separate generator and verifier identities and keys for promotion.

## Supply chain and original custody
Hash exact original bytes; record size, upload identity, origin and acquisition time. Never rename a different archive into a required source identity. Treat embedded scripts/instructions as untrusted inputs until assessed. Static inventory and safe bounded inspection precede execution; isolate build/runtime tests and review external calls, privileged commands, writable state and licenses.

Pin dependencies/artifacts where supported; preserve TLS/signature/checksum verification. Maintain component inventory including licenses, provenance, dependencies and known issues; do not claim an SBOM or vulnerability audit from a filename list. Uploaded evidence is not an attestation. Publish only explicitly classified public derivatives.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |
