# VFS_SERVER API

All responses are JSON. `/status` and `/ready` are operational probes. Other endpoints require the configured bearer credential when authorization is enabled.

## POST /artifacts
Writes an artifact through `adapter://vfs/artifact-write`.

Input: `path`, `content_b64`, `source`, optional `predecessor`, optional `media_type`.

Returns an actor receipt and `verification=PENDING_OBSERVER_READBACK`. It does not return PASS.

## POST /verify
Independent readback of a committed digest. Returns an `OBSERVER_VFS_READBACK` receipt.

## GET /artifacts/<sha256>
Returns artifact metadata and bytes after digest verification.

## GET /paths/<vfs-path>
Resolves a logical VFS path to the current artifact.

## GET /lineage/<sha256>
Returns predecessor lineage edges.

## GET /status
Process/storage counters and architectural identity.

## GET /ready
Checks storage writability, SQLite access and receipt-chain integrity.

## Error model
400 malformed/bounded-input error; 401 authorization failure; 404 unknown object/path; 500 internal invariant failure.
