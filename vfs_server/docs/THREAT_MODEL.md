# VFS_SERVER threat model

## Protected properties

1. artifact bytes remain bound to SHA-256 identity;
2. logical paths resolve to committed artifacts;
3. predecessor lineage cannot reference an unknown artifact;
4. actor commit and observer verification remain separate receipts;
5. receipt ordering is tamper-evident through the previous-receipt digest chain;
6. restart preserves committed state.

## Threats addressed

- path traversal;
- oversized writes;
- accidental object overwrite;
- object/database partial-write exposure;
- unknown predecessor injection;
- mutation without configured bearer authority;
- silent backing-object corruption detected during readback;
- receipt mutation/reordering detected by chain verification.

## Boundaries not claimed

This package does not by itself provide TLS termination, multi-tenant identity, distributed consensus, hardware-backed keys, remote replication, or Byzantine storage. Those belong to separate carriers/authority planes and must not be inferred from a local VFS PASS.
