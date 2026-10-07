# BRAINK development application node

The BRAINK development sector adds its own IDE, CLI and CI to the node architecture.
It is delivered on `feat/braink-application-node` in `Keddeh1/BRAINK-BETA-TEST`.
Uploaded source baselines remain in `baselines/`; function mapping is in `WORK_LOG.md`.

Each delivery has a separate package and clean build:

| Sector | Distribution | Implementation |
| --- | --- | --- |
| Core | braink-node-core | Registry, alignment, ingestion, indexing, checks, packets and ledger |
| CLI | braink-cli-node | `braink-node` commands and runtime operations |
| IDE | braink-ide-node | Workspace editing, revision checks, provenance and browser API |
| CI | braink-ci-node | Durable queue, source snapshots, stage processes, logs, artifacts and receipts |

## Website and runtime

Use your existing website at `/braink/development`, `/braink/ide`, `/braink/cli`,
and `/braink/ci`. Its native owner identity connects to the Keddeh runtime
application control plane, stored on the owner website server. The dedicated application worker executes sector builds on the owner
host, stores logs and receipts, and returns verified artifacts to the runtime.
The website displays actual queued, running and terminal results.

The IDE loads, creates and saves workspace files. Saves compare revisions and retain
before/after artifacts. The CLI executes the same installed commands on the owner host.
The CI snapshots source before execution; each sector is built in a fresh staging tree,
then installed into a fresh environment for its own tests. Core is an explicit dependency
of the CLI, IDE and CI distributions. Every receipt records source and artifact hashes.
Interrupted jobs receive terminal receipts; pending receipt uploads retry before new jobs.

## Build and install

```bash
python -m venv /path/to/build-tools
/path/to/build-tools/bin/python -m pip install setuptools wheel
/path/to/build-tools/bin/python scripts/build_sector.py --sector all \
  --run /path/to/new-build-run --artifacts /path/to/new-build-run/artifacts
/path/to/build-tools/bin/python scripts/qualify_installed.py \
  /path/to/new-build-run/artifacts /path/to/new-build-run all
python scripts/deploy_node.py --artifacts-dir /path/to/new-build-run/artifacts \
  --runtime-root /path/to/runtime --port 8765
```

The runtime workspace, ledger, queue and logs persist outside the source checkout.
`BRAINK_WORKSPACE`, `BRAINK_STATE_DIR`, `BRAINK_CI_AGENT_TOKEN`, `BRAINK_CI_WEBSITE`
and `BRAINK_CI_PYTHON` configure the worker. Website and worker credentials stay in
runtime secret storage. The existing owner authentication governs website operations.

## Commands

```bash
braink-node --workspace ./workspace --state-dir ./state init
braink-node --workspace ./workspace --state-dir ./state align ./workspace/projects/demo --name demo
braink-node --workspace ./workspace --state-dir ./state index
braink-node --workspace ./workspace --state-dir ./state ingest ./workspace/projects/demo
braink-node --workspace ./workspace --state-dir ./state check
braink-node --workspace ./workspace --state-dir ./state verify-ledger
braink-node --workspace ./workspace --state-dir ./state ci run --source /path/to/node --sector ide
braink-node --workspace ./workspace --state-dir ./state ci relay --source /path/to/node
```

CLI exit codes are 0 for success, 1 for a failed check/build, and 2 for invalid input.
The ledger adapter implements the baseline append contract with transactional SQLite
and a verifiable hash chain. Alignment retains the original `dekstop` API spelling,
metadata extensions and event names. Registry locking serializes concurrent alignment.
Ingestion and indexing use sorted traversal, exclude generated state and reject oversized
captures explicitly. Packet export validates shapes and prevents mutation through aliases.

## Process recovery

`scripts/supervise_node.py` runs the IDE and relay as separate supervised processes
and restarts either after process failure. `deployment/braink-development.service`
provides the Linux host startup configuration. The current owner runtime starts the
supervisor as a persistent process; host lifecycle evidence is recorded in the deployment.
The worker identifies HTTP requests as `BRAINK-CI/0.1` for the website transport.

The own-runtime branch trigger (`scripts/watch_branch.py`) follows the dedicated
GitHub branch and submits clean builds for changed sectors. Changes to core or shared
build/test scripts trigger all dependent sectors. Submissions retain stable IDs across
transport retries, and the relay exports the exact triggering Git commit before building.
The trigger retains local edits and follows only fast-forward branch updates.

## Deployment protocol

[PROTOCOL.md](PROTOCOL.md) defines the implemented function modules, module families, family variants, variant colonies and per-instance ceremonies. Clean sector builds also produce these hierarchical packages. The runtime supervisor can run the IL-LLM subscription mesh alongside the existing IDE, own CI relay and branch trigger. Each module occurrence, family, variant and colony receives a separate owner VFS store and independently read-back subscriptions.
