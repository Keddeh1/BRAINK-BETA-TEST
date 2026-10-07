# BRAINK IDE / CLI / CI application node

This is a separate application node hosted in BRAINK-BETA-TEST. Its runtime, distribution, workspace and ledger are independent of the owner-family engine.

## Delivery sequence

1. Preserve and map every unique baseline file and function.
2. Resolve core registry, ingestion, indexing, packet and ledger behavior.
3. Deliver CLI and IDE using the same core services.
4. Deliver BRAINK-owned CI with durable jobs and process execution.
5. Build core, CLI, IDE and CI from separate clean source staging trees.
6. Install each sector into fresh environments and exercise its tests.
7. Connect the existing website and runtime to the dedicated application worker.
8. Verify website-submitted builds, receipt recovery and artifact downloads.

The node uses its own persistent workspace, ledger, jobs and artifacts while joining
the existing architecture through the website and runtime adapters. Source definitions
and baseline metadata remain available for the owner systems.

## Every baseline file and function

| Baseline | Functions / methods | Resolution | Verification |
| --- | --- | --- | --- |
| `__init__.py` | No functions; comments only | Preserved in baselines; node package explicitly identified separately | Package imports from installed wheel |
| `paths.py` | `DekstopPaths`, `default_dekstop_paths` | Explicit root or environment; isolated workspace, no desktop assumption | Explicit path fixture and CLI init |
| `registry.py` | `ProjectEntry.to_obj`, `load_registry`, `upsert_project`, `store_registry` | Validate schema and duplicate IDs; preserve extension metadata; pure upsert; atomic write; parent creation | Create/update/load, malformed shapes and concurrent alignment |
| `align.py` | `_path_hash`, `AlignmentResult`, `align_project_into_dekstop` | Validate project directory; canonical comparisons; serialize registry update; ledger append | Missing path, idempotence, stable IDs and concurrent projects |
| `indexer.py` | `_stable_hash_text`, `InterlinkIndex.to_obj`, `build_interlink_index`, `write_index_artifact`, `ledger_index` | Sorted traversal before limiting; zero/negative limits handled; skip hidden/cache/link paths; exclude node artifacts; canonical content reference | Repeated index equality, self exclusion, artifact persistence and limit tests |
| `ingest.py` | `_read_bytes`, `artifact_ref_for_path`, `store_artifact_bytes`, `IngestedFile.to_obj` | Bounded reads reject oversize; streamed full-file hashing; verify hash against bytes; corruption rejection; exact captured byte count | Oversize without false ledger capture, valid/corrupt artifact tests, streamed digest |
| `ingest.py` | `iter_files`, `ingest_directory`, `ingest_file` | Deterministic directory order and pagination; validated offsets; reject file links; exclude node output/state; preserve captured bytes | Pagination, hidden paths, links, repeat ingestion and CLI lifecycle |
| `pass_runner.py` | `_read_json`, `PassFinding.to_obj`, `_finding_id`, `_discover_projects`, `run_dekstop_pass` | Handle non-object JSON and malformed registry shape; stable finding IDs; sorted project discovery; blockers for invalid metadata; root-missing finding; relative registry paths use workspace root | Missing root, malformed JSON/schema, registration gap, status load, optional ingestion and CLI thresholds |
| `plan.py` | `PlanningPacket.to_obj` | Validate action/scope/collections and JSON serialization; return detached export | Invalid packets and export mutation isolation; IDE edit-planning event |
| `result.py` | `ExecutionResult.to_obj` | Validate result fields and JSON serialization; return detached export | Invalid results and export mutation isolation; CLI check JSON and exit codes |

## Added node surfaces

- Core: canonical data, transactional ledger, atomic storage and serialized registry updates.
- CLI: initialization, alignment, ingestion, indexing, checks, ledger verification, IDE service and CI.
- IDE: file list/read/create/save, revision checks, provenance artifacts and browser controls.
- CI: durable source snapshots, atomic claims, stage subprocesses, timeout handling, logs, clean sector builds, installed qualification, artifact hashes and receipts.
- Website: `/braink/development`, `/braink/ide`, `/braink/cli` and `/braink/ci` connect to the existing runtime.
- Recovery: receipt outbox is flushed before new claims; the runtime returns existing claims to their worker; interrupted execution receives a terminal receipt.

## Verification

32 tests exercise actual subprocess success, failure and timeout, concurrency, recovery,
file operations and core behavior. Independent installed-package qualification runs the
core, CLI, IDE and CI suites against their respective clean-build artifacts. Runtime
queue tests execute SQL against SQLite and verify leases and receipt/artifact digests.
Final published versions and website execution evidence are recorded in `DEPLOYMENT.json`.

## Continuous branch integration

The dedicated own-runtime trigger follows `feat/braink-application-node`, determines
which sectors changed, and submits persistent job IDs to the website queue. Exact Git
commit exports feed the clean builds, preserving source identity even when later commits
arrive. A test executes a committed source export while retaining different local edits.
The process supervisor restarts IDE, relay and branch-trigger services independently.

## Function-module deployment protocol

Implemented addressable Python/browser functions, preserved compilation families, revision-pinned family variants and colonies, independent per-occurrence owner VFS stores and durable subscription ceremonies. Original lexical contexts remain executable; requests, returned values and exceptions receive instance VFS evidence. Completed ceremonies perform readback rather than republishing, and interrupted ceremonies resume their committed stages. Removed the CLI wrapper’s fixed overall deadline. Published and qualified the four sector packages through the existing owner website. A failed live VFS publication and a successfully verified replay remain in the evidence; its service-side error cause was not isolated. Actual mesh process restart preserved subscription and inbox state.

Final observed graph: 155 runtime function definitions, 30 source families, four variants, four colonies and 571 independently verified instance VFS stores. All 38 installed-wheel tests passed; all four website CI sector builds passed; 15 downloaded artifacts matched their hashes. A deployed SHA-256 function executed with request/return evidence in its own VFS.
