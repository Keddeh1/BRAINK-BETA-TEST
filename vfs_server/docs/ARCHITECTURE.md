# VFS_SERVER architecture

## Existing architectural contract

`VFS_SERVER` is the server-room role defined by the BRAINK deployment workset. Its operation is to mirror deployed files into the VFS artifact graph and bind lineage.

The package implements:

1. content-addressed immutable object storage;
2. logical VFS path -> current artifact binding;
3. predecessor lineage edges;
4. durable SQLite metadata with WAL + FULL synchronous mode;
5. atomic object writes;
6. hash-chained actor receipts;
7. separate observer readback receipts;
8. deterministic status/readback surfaces.

## Transition

AGENTIC_AI_SERVER:function_outputs
-> adapter://vfs/artifact-write
-> VFS_SERVER:artifact_graph
-> VFS_R12_ARTIFACT_MIRROR_RECEIPT
-> OBSERVER_SERVER:readback
-> BRAINK_SERVER:observer_memory

## Claim boundary

COMMITTED means the VFS actor committed an artifact and metadata transaction.
VISIBLE means an observer reread the persisted object and its digest matched.
Neither state implies runtime registration or external deployment; those belong to their own server roles.
