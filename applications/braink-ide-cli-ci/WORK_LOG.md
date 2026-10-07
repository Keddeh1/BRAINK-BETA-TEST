# BRAINK IDE / CLI / CI application node

This is a separate application node hosted in BRAINK-BETA-TEST. Its runtime, distribution, workspace and ledger are independent of the owner-family engine.

## Ordered work

1. Preserve the nine unique uploaded Python sources under `baselines/`. Complete. Duplicate sources were byte-identical; CPython 3.14 bytecode is not executable source.
2. Work through paths, registry, alignment, indexing and ingestion. In progress.
3. Work through pass findings, planning packets and execution results. Pending.
4. Supply explicit local hashing and ledger adapters; expose CLI commands. Pending.
5. Add a browser IDE backed by the same application services. Pending.
6. Add isolated CI, build a wheel, install and exercise the node. Pending.
7. Record deployment evidence and integration boundary. Pending.

## Architecture boundary

The application consumes a configured workspace and writes its own content-addressed artifacts and event ledger. Owner-runtime integration is an explicit adapter contract, not a replacement engine or an automatic modification to admitted owner packages. Existing KEX comments are preserved as source metadata, not execution instructions or verified scientific guarantees.
