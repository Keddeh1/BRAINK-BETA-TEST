# VFS_SERVER — allocated VFS fleet

`VFS_SERVER` is a **server of VFS instances** under `KEDDEH_SERVICE`. A queue submission receives its own allocated VFS ID and quota. The submitted baseline (A) and candidate (B) enter that VFS as a compressed A/B admission. A direct artifact POST is retired.

## Execution contract

1. The owner-authenticated controller calls `POST /vfs` with a label, queue source reference and optional byte quota. The response contains a distinct VFS ID.
2. It calls `POST /vfs/{id}/ab` with A and B bytes. A is zlib compressed. B is an A reference if identical; otherwise the carrier chooses the smaller of independent zlib and an A-relative XOR delta compressed with zlib.
3. The actor returns a pending observer state. The controller reads `GET /vfs/{id}/ab/{entry}`, validates both uncompressed SHA-256 digests, then calls `POST /vfs/{id}/ab/{entry}/verify` for separate observer receipts.
4. The queue workflow records the VFS ID, entry ID, compressed byte count, source digests, actor receipts and observer receipts. It must not mark execution verified from allocation or actor write alone.

Each instance has its own SQLite WAL metadata, content objects, path namespace and receipt chain under `instances/{vfs_id}`. The allocator registry records IDs, source references, quotas and A/B entries. It never resolves a caller supplied filesystem path. The prior `VFSStore` remains the internal content-addressed adapter `adapter://vfs/artifact-write`.

Run: `python -m vfs_server.server --root .vfs-server --host 127.0.0.1 --port 8787 --token-file /run/secrets/vfs_token`.
Tests: `python -m unittest discover -s vfs_server/tests -v` and `node --test vfs_server/web/*.test.mjs`.

The public HTML surface must call an owner-authenticated same-origin server route; that route holds the bearer credential and forwards to VFS_SERVER. Never embed the token in HTML, issue bodies, or receipts. Non-loopback listeners require `--token-file`; local loopback without one is a development mode. A single writable volume and one process are assumed. This package does not claim multi-replica consistency or production deployment.

The new A/B carrier is an explicit implementation of the user's allocation and compression correction. The supplied archival sources establish VFS projection, structural KEX packet compression, and observer readback; they do not supply a byte-for-byte A/B codec specification. The codec here is version one and is described precisely in `docs/ARCHITECTURE.md`. A later codec can be added with an explicit version without reinterpreting old entries.
