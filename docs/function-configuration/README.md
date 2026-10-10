# Function configuration and execution qualification

This branch repairs available BRAINK modules and the repository's VFS server. It does not replace the separately referenced `/opt/braink/modules/kex_wbos/capability_runner.py`, `kex.cli.main` mesh CLI or `kex-secret-resolver`; those sources are not in this repository's inspected main tree. Native KEX seed-to-execution derivation remains a source-acquisition task. Existing numerical hardware ring levels 0–3 are retained; they are not one-origin logical addresses.

| Module/function group | Configuration and checked behaviour | Remaining scope |
|---|---|---|
| core.rings: constructors, properties, can_access | Existing documented privilege order: source ≤ target; all sixteen pairs checked | Python simulation, not CPU privilege enforcement; memory intervals are descriptors |
| domain.engine: initialize/get_ring/validate_transition | Retained four-ring layout and explicit initialization | No allocation of physical RAM; no native lineage admission inferred |
| domain.dispatcher: register_module | Nonempty module/executor identity, unique registration | input_spec/output_spec remain descriptive, no general schema interpreter |
| domain.dispatcher: dispatch | Registered definition, unique dispatch ID, mapping input | In-process mutable records; concurrent use not qualified |
| domain.dispatcher: execute_dispatch | Explicit local callable map keyed by WorkModule.executor; dependencies require completed module; completed only after mapping result | No remote executor, durable queue or automatic retry; no arbitrary import or command execution from seed |
| domain.dispatcher: get_dispatch_status | Pending/completed/failed record lookup | Private audit persistence needs separate integration |
| runtime.executor: execute/operation_count | Existing ring context, now uses corrected hierarchy | Python callable execution does not isolate a hostile process |
| utils.common and exceptions | Existing formatting/validation and exception interfaces retained | Unchanged functions are inventoried, not all newly qualified |
| vfs_server.server: create_server/main | Per-server isolated handler bindings; token-file CLI matches compose/Kubernetes configuration; loopback default | No externally published service; local no-token development mode retained |
| Handler: GET/POST | Existing authorizer gates artifact reads, writes and verification; status/readiness public | Bearer gate is transport access, not a substitute for contextual KEX derivation; TLS needs external terminator |
| store/model/observer/backup/qualification | Existing code preserved and function-inventoried; storage/receipt restart tests run | Broader concurrency, power-loss and source-identity semantics need independent qualification |
| packaging | Discover braink and vfs_server subpackages; omit invalid empty author email | Build is not deployment |

Configure local execution by constructing `WorkModuleDispatcher({'name': trusted_callable})`, registering a WorkModule with executor='name', then dispatching. Existing callers that relied on automatic unregistered dispatch or fake completion must explicitly register modules and bind an executor. This intentional compatibility change makes missing configuration visible as failure instead of a success receipt. Dependencies name module identities, not dispatch identities. A failed dispatch is retained; retry needs a new dispatch identity. No exception text or secrets are emitted in status.

VFS launch: `python -m vfs_server.server --root /path/to/private/state --host 127.0.0.1 --port 8787 --token-file /path/to/private/token`. Keep token files out of Git. The existing deployment manifests already supply that option. Do not infer credentials from document content or enable financial execution while configuring this prototype.

Validation: 25 tests pass across tests and vfs_server/tests. An authenticated loopback HTTP test checks denied unauthenticated writes/verification, authorized write/readback, receipt verification and restart content retention. Exhaustive ring comparison and real-dispatch/failure/dependency tests are included. Wheel builds successfully and imports plus ring smoke check pass from a separately installed target outside this checkout. Original failures included inverted ring comparison, fake dispatch completion, literal backslash-n imports, missing token CLI/handler wiring and invalid package metadata. Repair uses existing declared semantics rather than changing owner's number-line or replacing source-local lineage rules.

Function inventory records source lines, signatures, docstrings, called functions, explicit raises and hashes. Static inventory is not a dynamic coverage certificate. It is generated in the SERVERSPACE formal sector register and mirrored here for this source revision.

## Fault and concurrency qualification, revision 0.2

New checks cover 32 simultaneous shared-carrier writes with separate path/source metadata, 128 concurrent executor successes, failed replacement, rollback after staged binding writes, a subprocess exiting before transaction commit, corrupted carriers and tampered receipts. Backup now stages only carriers referenced by the database snapshot, verifies each staged digest, and atomically replaces its output. Sixteen writes committed after snapshot acquisition remain outside that snapshot, as expected. Failed backups preserve an existing output.

Path bindings now retain each path's source, predecessor, media type and creation time separately from content hashes. `resolve_path` and write results reflect that binding; `get_artifact(digest)` retains the legacy carrier record and `lineage(digest)` returns aggregate carrier edges. Neither digest-only method is a contextual execution authority. Existing databases populate binding rows from legacy recorded metadata; lost historical distinctions cannot be recovered by migration alone. Receipts should be used to investigate such prior provenance.

Immutable orphan objects may survive failed or interrupted transactions; they are not reachable through an admitted binding and are excluded from backups. Safe orphan reclamation is not implemented because deleting concurrently used carriers requires separate coordination. Tests simulate process exit and selected OS exceptions, not physical power loss or a compromised host. Successful threaded counter updates do not make arbitrary user callables thread-safe. Full current suite: 38 cases passed.
