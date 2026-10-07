# BRAINK IDE / CLI / CI application node

This is a separate application node hosted in BRAINK-BETA-TEST. Its runtime, distribution, workspace and ledger are independent of the owner-family engine.

## Ordered work

1. Preserve the nine unique uploaded Python sources under `baselines/`. Complete. Duplicate sources were byte-identical; CPython 3.14 bytecode is not executable source.
2. Work through paths, registry, alignment, indexing and ingestion. Implemented and locally verified.
3. Work through pass findings, planning packets and execution results. Implemented and locally verified.
4. Supply explicit local hashing and ledger adapters; expose CLI commands. Implemented and locally verified.
5. Add a browser IDE backed by the same application services. Implemented and HTTP-tested.
6. Add isolated CI, build a wheel, install and exercise the node. Local wheel and tests pass; GitHub results tracked below.
7. Record deployment evidence and integration boundary. Deployment script implemented; runtime readback follows qualification.

## Architecture boundary

The application consumes a configured workspace and writes its own content-addressed artifacts and event ledger. Owner-runtime integration is an explicit adapter contract, not a replacement engine or an automatic modification to admitted owner packages. Existing KEX comments are preserved as source metadata, not execution instructions or verified scientific guarantees.

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

- Local `LedgerStore`: transactional concurrent append, chained SHA-256 references and verification. These are local adapter semantics, not a claim of equivalence to an unavailable owner KEX implementation.
- CLI: init, align, index, ingest, check, verify-ledger and serve. JSON output and CI exit status use the same services as the IDE.
- IDE: file list/read/create/save, optimistic revision checks, before-and-after artifacts, planned/completed edit events, index/check/ledger controls. Loopback by default; remote binding requires a token. UTF-8 editor, no debugger or terminal yet.
- CI: isolated wheel build and installed-package tests on Python 3.10/3.12/3.14, coverage floor and command smoke checks.
- Deployment: private Linux process with its own venv, workspace/state, PID/log and health readback. Public ingress and reboot supervision are not installed by this release.

## Local qualification

The installed wheel passed the initial 21-test suite with 94% statement coverage. An additional concurrent registry update test was added before final qualification. GitHub CI results and final deployed wheel digest are recorded in `DEPLOYMENT.json` after verification.
