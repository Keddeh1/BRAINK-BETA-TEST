# Crash recovery, KEX projections and service agreements

This release extends the supplied KEX terminal, HTML Linux carrier, V76 resident
projection and R36 HTTP multiplexer. Original admitted owner files remain unchanged;
shared scripts add live controls and durable permission boundaries. The deployment
scope is nine repository families on the current cloud host. Off-site operation
requires a separately configured host and security boundary; the current VFS
binding intentionally accepts only the local owner endpoint.

## Boundary packages and acceptance

| Boundary | Package/control | Recovery and verification |
|---|---|---|
| Before bilateral intent publication | Durable intent, atomic replace, file and directory fsync | No actuator call occurs before intent persistence; interrupted staging is not admitted |
| Intent saved before first register call | Retained command prefix and exact nonce | Reconstruct from durable pending cycle rather than sample new telemetry |
| Register commit before acknowledgement save | R36 journal idempotency plus retained nonce | Injected crash repeats the exact command identity; one distinct register effect |
| Acknowledgement prefix saved | Resume from recorded actor count | Existing prefix retained; remaining commands only |
| Final actor acknowledgement before namespace receipt | Digest-bound cycle request identity | Finalization uses the immutable pending payload identity |
| Namespace commit before cycle-state save | Registry request lookup and integrity replay | Return original receipt after restart, including an intervening launch receipt; reject changed payload |
| Cycle completed before next sample | Atomic last/pending transition | Completed cycle advances once; next cycle samples fresh telemetry |
| Owner feedback unavailable | Paused retry without synthetic observations | No new actor calls from unavailable feedback; durable unfinished intent retained |
| Owner explicitly pauses or disconnects | Durable enable flag and pipeline fence | Pause/disconnect survives reconstruction; explicit reconnect required |
| In-flight actor during disconnect | Serialized bounded admission | Disconnect acknowledges after admitted command exits and fence fsync completes; already committed work is retained |
| Stale projected commands after reconnect | Monotonic pipeline generation | Reject commands using an earlier generation |
| Agreement withdrawal or user-space mismatch | Versioned owner-space permission record | Reject projected mutation after revocation or with a customer-space context |
| Owner process exits inside a network domain | Docker restart and preserved state mounts | Owner code, dual networks and durable phase retained; bounded worker heaps |
| Intermediate domain or upstream bridge disappears | Existing flywheel and controlled reanchor | Child state continues; genesis and downstream domain persist; no unbounded expansion |
| Domain memory pressure | 256 MiB hard limit, 32 MiB Node heaps, 16 MiB probe heap, 64 PIDs | Enforce the same policy on existing owned domains and newly created domains |
| Slow bootstrap or domain readback | Separate bounded control and startup budgets | 120-second bootstrap/domain operation budget; 90-second controller startup budget; fast HTTP probes retain 8 seconds |
| VFS interruption or unverified concurrent append | Durable cursor, hash-before-ack and verified SQLite snapshot | Preserve subscriber cursor and immutable local mirror; original snapshot regression suite remains required |
| Cloud task/controller loss | State retained plus repeatable family launcher | Controllers must restart in a new task; Docker domain restart policy alone does not supervise host Python controllers |
| Browser or projection tab disappears | Server-owned intents and memory-only browser credentials | Closing HTML cannot discard server receipts; a disconnect must receive an explicit successful server acknowledgement |
| Permission or hosted workflow startup denial | Recorded external gate and local qualification | Never infer hosted success from local tests or issue write permission |

The final two operational boundaries remain explicit limitations until persistent
host supervision and the external hosted capability are independently qualified.
No statement here claims physical power generation, multi-host isolation or an
already deployed off-site service.

## Functions and user boundaries

All gateway operations require the private owner runtime token. Customer forms
are separate and do not issue owner credentials. The owner kernel routes pipeline,
projection and agreement functions through its existing mapped-request path.

- `pipeline` reads connected state and generation. `connected:false` plus a bounded
  reason persists a disconnect. `connected:true` explicitly reconnects and advances
  generation. Readback and owner stop remain available while disconnected.
- `projection` maps the three supplied HTML engines and R36 multiplexer to their
  execution locations, agreement boundary and actor permissions. Off-site
  observation is marked unconfigured, with no actor credentials.
- `agreement` returns operational terms. Accept or revoke with `version:"1.0"`
  and boolean `accepted`. Acceptance records owner space, authenticated principal
  and UTC time in private durable state; no customer data is collected here.
- HTML controls attach `projection_context` with owner space and agreement version,
  and the current `pipeline_generation`. Mutating projected requests require current
  acceptance. Direct authenticated owner automation retains its existing admission
  authority; this token is not suitable for untrusted tenants.

The HTML panel displays purpose, execution location, scope, data handling, retention,
withdrawal and disconnect semantics before acceptance. Acceptance is an operational
permission record, not an invented legal service contract. Revocation blocks future
projected mutations. Disconnect additionally blocks gateway and bilateral actor
admission. Neither action erases committed work or receipts.

A disconnect is a software command fence at the authenticated gateway and bilateral
loop. It does not cut physical links, revoke already dispatched register work, fence
other trusted local processes that directly use the raw R36 endpoint, or isolate a
compromised host. Off-site security requires scoped credentials, network policy and
an independently reachable control plane. No arbitrary remote URL is accepted by
this release.

## Operation

Connect in the preserved HTML panel, read **Service agreement**, then use
**Accept service agreement** for owner-local projection commands. **Projection
services** shows placement and scope. **Revoke projection permission** withdraws
projection authority. **Disconnect pipeline** durably fences command admission
and clears the browser token after successful acknowledgement. To reconnect, use
**Connect** and then **Reconnect pipeline**; revoked agreements still require a new
acceptance. A timeout or browser closure is not disconnect confirmation: read the
pipeline status using an authenticated owner session.

Private files: `state/pipeline-gate.json`, `state/projection-agreement.json`,
`state/bilateral-runtime.json`, registry journal, admitted owner sources and domain
state. Preserve them through deployment and rollback. Do not copy credentials into
public repositories or public frontage.

**Next task: qualify and roll out the complete recovery package across all nine families, then verify persistent host supervision.**
