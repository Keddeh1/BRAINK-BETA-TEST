# VFS_SERVER fleet and A/B compression

## Topology

`VFS_SERVER` allocates multiple VFS instances. The queue submission is the source reference. Each allocated instance owns a separate backing `VFSStore`; its A/B entries are addressed by `vfs_id` and `entry_id`. The prior content-addressed object graph is an internal adapter rather than the public intake contract.

`QUEUE:submission -> VFS_SERVER:allocate -> VFS:{id} -> A/B admission -> actor receipts -> reconstructed readback -> observer receipts -> queue evidence`

## Codec v1

A is `zlib(A)`. If `SHA256(A)==SHA256(B)`, B is `reference:A` with no second object. Otherwise B is stored as the smaller of `zlib(B)` and `zlib(XOR(A,B))` when the sides have equal length. The second option is tagged `xor+zlib`, is reconstructed with A, and is rejected if either source digest or object digest fails. This is lossless compression of the A/B pair, not a raw VFS commit. Compression savings are measured against `len(A)+len(B)`; no savings are claimed for arbitrary input.

The per-instance SQLite registry stores source reference, digests, codec, compressed object digests, lengths and stored byte count. The object store uses atomic writes, WAL metadata and hash-chained actor receipts. Registry admission follows readback of both compressed frames. The observer route rereads the persisted objects and reconstructs both sides, then records distinct observer receipts. An interruption before registry admission may leave unreferenced content objects; it cannot yield an admitted A/B record.

## Governance and scope

The HTTP bearer gates allocation, list, read and observer operations. The server accepts generated hex IDs, never user filesystem paths, for instance lookup. Its host role and transport are reported as `KEDDEH_SERVICE / KEDDEH_SYSTEMS / VFS_SERVER / HTTP`. A Site owner route is the authority boundary for the browser; the bearer stays server-side. The queue retains its separate review and execution gate. An admitted A/B entry is evidence of VFS custody, not permission to actuate a GitHub target or evidence of deployment.

This implements an explicit A/B codec v1. The archival source described structural KEX packet compression but did not establish this exact byte codec. A future codec needs a stored version and a compatibility reader before migration.
