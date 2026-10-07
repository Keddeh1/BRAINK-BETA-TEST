# KEDDEH owner-family package

This package executes the owner's K-Cloud components, supplied workstation runtimes, R36 actuator, MCP estate, broker/agent boot lifecycle, periodic observer and workbook as a persistent server family. A family includes ten admitted workstation services and a recursive three-domain chain with three isolated workstation processes in each domain. The owner's zeroless router governs control dispatch; bilateral feedback persists its intent and completed prefix, and VFS_SERVER holds mirrored artifacts and subscription cursors.

The deployment vessel is Linux/Python 3.12/Node 24/Docker. Runtime state, private keys, credentials and customer data belong outside the source tree. Original private owner sources live in the private bundle. Public repositories carry public engine derivatives, wheel, launch manifests, documentation and custody hashes. Do not copy the private source bundle into a public repository.

## Installation and activation

Install uv 0.12.19, then run `UV_CACHE_DIR=/workspace/.cache/uv uv sync --frozen` in the engine checkout. The committed wheel can instead be installed with dependency versions from uv.lock. Each repository's `.keddeh/launch-family.sh` starts its own admitted family through the engine. Configuration supplies its repository identity, private runtime root, distinct port offset and VFS endpoint/token-file reference. `KEDDEH_ENGINE_ROOT` selects the engine checkout. Credentials are provisioned in private state, never in JSON committed to Git.

## Operator journeys

Use the preserved terminal's `cloud auth`, then `cloud status` for actual readiness. `cloud bilateral status` shows retained cycle state; `cloud bilateral start` resumes continuous actuation and `cloud bilateral pause` preserves unfinished intent while stopping future side effects. `cloud domains` reads the actual recursive network family. `cloud hci` renders the Shared KEDDEH console using live readbacks. Register commits use `cloud commit NODE NONCE TENANT`; retries with the same tuple use the original R36 durable receipt. `cloud observer` and `cloud workbook` use the supplied owner modules. `cloud propagate` runs the supplied propagation abstraction; `cloud enact` maps its output to software registers.

The runtime gateway requires its private token. Runtime administration and private estate tools are owner functions; customer-facing APIs are separately scoped and must not expose these credentials or operations. No email or external messaging is sent by this package.

## VFS contract

VFS_SERVER retains its existing identity `WM.DEPLOY_VIRTUAL_SPACE.R1`, `adapter://vfs/artifact-write` and artifact graph. A write returns actor evidence; GET artifact readback verifies SHA-256 and POST /verify emits the separate observer receipt. Each deployment subscribes durably to `/packages/web4`, polls sequenced receipt events and mirrors package bytes to its private content-addressed cache. Its cursor is saved locally before acknowledgement, so interrupted polling can replay safely. A subscriber caches and verifies package updates; it does not silently execute them or replace an active runtime. Qualified promotion remains explicit. Family readbacks sync under `/families/<family-id>/readback.json` with predecessor lineage.

## Recovery and field use

Use families for development, evaluation, internal server operation and controlled runtime qualification. Each family has a separate mutable root and credentials. Local domain networks and process heaps are isolated; the families still share one physical cloud host. Test domain loss with `scripts/verify_owner_domains.py`; it restores its test chain afterward. On process exit, owned service recovery retries at a bounded rate; domain restart policy retains phase/epoch files. On VFS unavailability, local actuation continues and synchronization retries without advancing an unprocessed cursor. Preserve journals and state during updates; do not replace them with bundle contents.

Physical SD-card flashing, FROST threshold signatures, hardware watchdogs, Anycast/BGP and independently assessed public production operation are architectural bindings requiring their real targets. The deployed PLL is software state, the R36 registers are software actuators, and neither is presented as physical electrical generation. Use the process/action/configuration contracts for exact inputs, readbacks, operational fit and limitations.

## Qualification

`python scripts/qualify_release.py --output /outside/source/new-directory --runtime-root /private/family-root --container-no-sandbox` checks frozen installation, controlled documents, source and installed-wheel tests, actual package processes, browser interactions and recursive domain recovery. The sandbox flag is only for the isolated cloud Chromium test container. Evidence records exact source commit, artifact hashes and individual outcomes. GitHub billing currently prevents hosted Actions startup; local qualification is recorded separately. Public-site publication and independent assessment require their own readbacks.
