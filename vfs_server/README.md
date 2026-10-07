# VFS_SERVER

Implementation of the existing BRAINK server-room identity `VFS_SERVER`.

Architectural bindings:
- server: `VFS_SERVER`
- module: `WM.DEPLOY_VIRTUAL_SPACE.R1`
- target: `VFS_SERVER:artifact_graph`
- adapter: `adapter://vfs/artifact-write`
- required receipt: `VFS_R12_ARTIFACT_MIRROR_RECEIPT`
- observer: `OBSERVER_SERVER`

The package mirrors deployed files into a content-addressed artifact graph, records SHA-256 identities, preserves predecessor lineage, emits hash-chained receipts, and exposes independent readback.

No new runtime or revision identity is allocated here.

Run: `python -m vfs_server.server --root .vfs-server --host 127.0.0.1 --port 8787`

Test: `python -m unittest discover -s vfs_server/tests -v`

A write receipt is actor evidence, not verification. Verification is a separate observer readback.
