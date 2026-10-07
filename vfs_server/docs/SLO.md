# VFS_SERVER service objectives

These are engineering objectives, not measured production claims.

## Availability objective
- readiness endpoint suitable for orchestration gating;
- no promotion to service-ready when SQLite, storage writability or receipt-chain integrity fails.

## Durability objective
- artifact bytes are fsync'd before metadata commit;
- SQLite uses WAL and synchronous=FULL;
- observer readback recomputes SHA-256 from backing bytes;
- backup captures a SQLite-consistent database plus immutable objects.

## Integrity objective
- content address is SHA-256 of artifact bytes;
- unknown predecessor is rejected;
- receipt chain is independently recomputable;
- digest mismatch is a contradiction, never PASS.

## Recovery objective
A restored instance must pass `python -m vfs_server.qualification` and required observer readbacks before mutation traffic resumes.

Latency, throughput, RPO and RTO are NOT YET MEASURED and must not be claimed until deployment telemetry establishes them.
