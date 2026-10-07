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

## HTTP carrier and authorization

The server is a real host adapter: POST /artifacts writes content-addressed bytes and returns actor evidence; GET /artifacts/{digest} reads the stored bytes; POST /verify performs a separate observer readback and appends an observer receipt. /paths/{path} and /lineage/{digest} resolve the graph. /status and /ready provide health. Artifact reads, writes, and verification require the configured bearer token. The browser carrier can call these operations through an authenticated Site server route; do not put the token in HTML or a queue issue.

For local development, the default loopback listener may run without a token. A non-loopback listener requires --token-file at startup. Docker Compose and Kubernetes manifests bind the token as a secret; provision it out of band before applying Kubernetes resources. The data volume must be writable by UID/GID 10001. The write receipt is not observer verification: inspect the /verify response and persisted receipt chain separately.

The source uses a synchronous HTTP server and SQLite WAL. Do not claim distributed coordination or exactly-once writes across multiple replicas. The Kubernetes manifest intentionally has one replica and a ReadWriteOnce volume.
