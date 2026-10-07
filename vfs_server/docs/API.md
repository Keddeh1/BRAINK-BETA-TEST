# VFS_SERVER HTTP API

`/status` and `/ready` expose process status. All VFS operations require the configured bearer token. JSON responses carry `service_environment.classification=KEDDEH_SERVICE`.

| Method | Path | Meaning |
| --- | --- | --- |
| POST | `/vfs` | Allocate one isolated VFS. JSON: `label`, `source_ref`, optional `quota_bytes`. Returns `allocation.vfs_id`. |
| GET | `/vfs` | List allocations. |
| GET | `/vfs/{id}` | Inspect allocation and quota. |
| POST | `/vfs/{id}/ab` | Enter A/B. JSON: `a_b64`, `b_b64`, `source_ref`. Returns entry and actor receipts, with `PENDING_OBSERVER_READBACK`. |
| GET | `/vfs/{id}/ab` | List A/B entries in the allocated VFS. |
| GET | `/vfs/{id}/ab/{entry}` | Reconstruct A and B; return their base64 bytes and verified digests. |
| POST | `/vfs/{id}/ab/{entry}/verify` | Independently reread backing objects, verify compressed object SHA-256 and reconstructed A/B digests, emit observer receipts. |
| POST | `/artifacts`, `/artifacts/raw`, `/verify` | HTTP 410. Direct artifact commit is retired. |

IDs are 32 lowercase hex characters allocated by the server. A and B each have a 32 MiB input limit. Quota is measured over the stored compressed frames of accepted entries. The content adapter may hold unreferenced frames if a write is interrupted before registry admission; maintenance must reclaim only frames not referenced by an admitted entry. A 201 response records actor evidence; verification is a separate step.

Errors: 400 invalid input or quota; 401 unauthorized; 404 unknown allocation or entry; 410 retired raw commit; 500 internal invariant failure. A production reverse proxy should impose a request body and rate limit. `/ready` currently reports allocator initialization, not a full disk, chain, or replica health proof.
