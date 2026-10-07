# VFS_SERVER operations

## Start

`python -m vfs_server.server --root /var/lib/keddeh-vfs --host 127.0.0.1 --port 8787 --token-file /run/secrets/vfs_token`

The bearer-token gate protects mutation and explicit verification endpoints when a token file is configured. Secret material is never committed to the repository.

## State

- immutable objects: `ROOT/objects/<sha256 fanout>`
- metadata/paths/lineage/receipts: `ROOT/vfs.sqlite3`
- SQLite mode: WAL
- SQLite synchronous mode: FULL

## Backup

Stop mutation traffic or take a SQLite-consistent backup, then preserve both the database and object directory. A database without its objects is incomplete state; objects without metadata lose path/lineage/receipt state.

## Recovery

1. restore database and objects together;
2. start the server against the restored root;
3. run `python -m vfs_server.qualification`;
4. verify required artifacts through OBSERVER readback;
5. only then return the service to mutation traffic.

## Failure states

- `object_digest_conflict`: quarantine backing store;
- `readback_digest_mismatch`: do not promote VISIBLE;
- `unknown_predecessor`: reject lineage mutation;
- `receipt_chain_mismatch`: quarantine evidence ledger;
- authorization failure: HTTP 401; no mutation attempted.
