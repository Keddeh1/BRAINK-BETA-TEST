---
document_id: OPS-001
title: Operations, incidents and recovery
revision: 1.0
status: Issued
classification: Public
accountable_owner: Keddeh1
issued_on: 2026-10-07
review_due: 2027-10-07
timezone: Australia/Adelaide
approval_basis: Owner instruction to establish enterprise governance; independent review pending
---

# Operations, incidents and recovery

## Operational ownership
Each environment requires named owner/operator, service inventory, source/configuration revision, network/storage scope, access and trust distribution, monitoring, backup, incident routing and approved runbooks. No production environment exists merely because a Compose file was rendered.

Observe health through representative authenticated requests and real bytes/readbacks. Capacity, free space, quotas, replication and failure domains require separate evidence. Alert on failed gates, replay/corruption, stale observations, resource limits, abnormal access and restore failure. Alerts and response routing remain unimplemented unless actually configured.

## Incident control
Severity 1: confirmed integrity compromise or widespread production loss. Severity 2: material service loss or suspected compromise. Severity 3: contained defect/degraded service. Operator records detection, scope, owner, timeline, evidence custody, containment, recovery and communications. No fixed contractual response SLA is asserted without an agreed staffing model.

Preserve evidence before destructive remediation where practicable. Emergency change authority and retrospective review apply. Document cause and corrective/preventive actions without replacing original observations.

## Recovery
Backup actual objects, registry events, assessment receipts, trust/checkpoints and needed original sources. Restore into an isolated target; validate complete roots/parents/signatures and functional reads before promotion. A valid partial restore remains unpromoted. Test restore at least quarterly and before material storage/recovery changes.

Define RPO/RTO per service through impact analysis and provisioned resources; current values are unassigned. Same-host local recovery tests do not prove independent archive resilience. No generation pruning or automatic retention deletion before recovery/hold/authorization checks.

## Change history

| Revision | Date | Change | Basis |
|---|---|---|---|
| 1.0 | 2026-10-07 | Initial governance baseline | Owner establishment instruction; independent review pending |
