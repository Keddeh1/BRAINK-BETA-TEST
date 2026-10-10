# BRAINK - KEX_SEED Ring Architecture Bootstrap

This repository bootstraps work for implementing the KEX_SEED Ring Architecture (Ring 0..3) and the Domain/Runtime Engines described in the provided architecture notes.

Files added by the bootstrap:

- ARCHITECTURE.md    — full architecture and deep dives (source content provided)
- sims/ring1_sim.py   — Python validation simulation skeleton for Ring 1 invalid-access scenario
- docs/TODO.md       — next steps and implementation checklist
- requirements.txt   — minimal Python requirements
- .gitignore         — python ignores
- LICENSE            — MIT License

See ARCHITECTURE.md for the original specification and deep-dive text.

Function configuration and qualified local execution paths are documented in [docs/function-configuration/README.md](docs/function-configuration/README.md). This distinguishes tested runtime behaviour from descriptors, source references and deployment declarations.
# MCP SDK service adapter

The optional Python MCP SDK adapter delegates VFS operations to the existing HTTP
service and executes those calls through `RuntimeExecutor` at ring 2. It does not
create another store. Requires Python 3.10 or later:

```sh
python -m pip install '.[mcp]'
python -m braink.mcp_service --vfs-url http://127.0.0.1:8787 --token-file /run/secrets/vfs-token
```

Start the existing `vfs_server.server` with the matching token file. The adapter
uses stdio; its trusted local MCP client inherits that credential's VFS authority.
Remote backing services require HTTPS, and redirects are rejected. Credentials
are loaded from the file, never accepted as tool arguments. This setup does not
change the existing HTTP server's authentication policy or deploy a public MCP endpoint.

Tools: `vfs_status`, `vfs_resolve`, `vfs_binding_history`, `vfs_write`, `vfs_verify`,
and `runtime_status`. Runtime status describes this adapter's executor, not the
whole estate. Write parameters retain the HTTP contract's `content_b64`, source,
predecessor, media type, continuation ID, and expected version. Identical retries
return their original receipt; changed continuation inputs or stale versions fail.
Readback verification remains a separate observer operation.

Run the complete qualification including the real SDK client/server handshake:

```sh
python -m pytest tests vfs_server/tests -o addopts='' -q
```
