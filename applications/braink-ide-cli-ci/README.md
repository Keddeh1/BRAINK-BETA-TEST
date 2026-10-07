# BRAINK IDE / CLI / CI application node

An added application node in the BRAINK sector. It has its own package, process,
workspace, state and event ledger. `node.json` describes the node interfaces.
The uploaded originals remain in `baselines/`; executable implementations live
in `src/braink_node/`. No owner-family engine is replaced.

## Install and operate

```bash
python -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/braink-node --workspace ./workspace --state-dir ./.braink-node init
.venv/bin/braink-node --workspace ./workspace --state-dir ./.braink-node serve
```

Open `http://127.0.0.1:8765` on the same host. The browser workspace loads and
edits UTF-8 files, creates files, refreshes the index, checks the workspace and
verifies the ledger. Saves retain before-and-after artifacts and reject a stale
revision. Files are limited to 1 MB for editing. This first IDE version does not
provide a terminal, language server, debugger or remote collaboration.

Register and ingest a project with the same service functions:

```bash
braink-node --workspace ./workspace align ./workspace/projects/demo --name demo
braink-node --workspace ./workspace index
braink-node --workspace ./workspace ingest ./workspace/projects/demo
braink-node --workspace ./workspace check --fail-on warn
braink-node --workspace ./workspace verify-ledger
```

Set `BRAINK_WORKSPACE` and `BRAINK_STATE_DIR` or use the global options before the
command. State must be isolated from the source workspace; a hidden state directory
or a directory outside the workspace is recommended. Ingestion skips hidden paths,
cache directories and symbolic links; visible artifacts and the ledger are excluded
when they reside inside a source root. Traversal is sorted at each directory before
applying limits. Oversized artifacts are rejected, never silently truncated.

CLI exits: `0` successful operation or passing check; `1` findings reach the check
threshold; `2` input or filesystem error. `check` checks node workspace metadata
and project registration, not arbitrary project test suites. GitHub CI separately
tests and builds this application on Python 3.10, 3.12 and 3.14.

## Deploy the independent process

```bash
python -m pip install build
python -m build
python scripts/deploy_node.py --wheel dist/braink_application_node-0.1.0-py3-none-any.whl \
  --runtime-root /path/outside/git/braink-ide-cli-ci --port 8765
```

The deployer installs the wheel into a private venv, initializes the workspace and
starts a detached loopback process. Runtime logs, PID and deployment evidence live
under the runtime root. It does not install a reboot supervisor or public ingress.
For remote binding, `serve --host 0.0.0.0` requires `BRAINK_NODE_TOKEN` of at least
32 characters; API calls use `Authorization: Bearer ...`. Configure TLS ingress on
the target host before exposing remote access. The token stays out of Git and is
entered in the browser access field; it is not persisted by the UI.

## Integration contract

The local SQLite ledger supplies `append(event_type, route, payload) -> event_ref`.
This explicitly replaces the unavailable baseline dependency inside this node only.
It retains baseline event names and packet fields for adapters. The hash chain
detects modified event bodies during verification; it is not externally anchored
and cannot detect complete historical replacement or tail deletion. Registry writes
are atomic, and alignment updates share a process lock. Registry writes and ledger
events are separate transactions; a crash may require replaying alignment.

The original `dekstop` API spelling and metadata comments are retained for mapping.
No formal KEX invariants are asserted by this implementation. Owner runtime binding
requires an explicit integration adapter; launching this process does not admit or
promote it into the owner's qualified execution manifest.

## Verify

```bash
python -m pip install build coverage
python -m build
python -m pip install dist/*.whl
coverage run --source=braink_node -m unittest discover -s tests -v
coverage report --fail-under=80
```

See `WORK_LOG.md` for the ordered implementation and function-by-function mapping.
