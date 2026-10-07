# VFS_SERVER deployment validation — 2026-10-07

Source: `Keddeh1/BRAINK-BETA-TEST`, branch `codex/vfs-server-host-boundary`, draft PR #1, observed head `a8066d1a3e0ca7e13c2e3fccb450b13751f6ccb3`. This is an actor-side validation report, not a deployed-service receipt or independent assessment.

## Executed checks

| Check | Result | Evidence and limit |
| --- | --- | --- |
| Python source compilation | PASS | All 11 top-level `vfs_server/*.py` modules compiled in memory. Does not execute imports or persistence. |
| A/B reversibility | PASS | Exhaustive 1,022 binary patterns across lengths 1–9 round-tripped; graph origin remained powered, unaddressable `1 > 2`. Pure codec only. |
| HTTP allocation and actuation | PASS in isolated harness | Real localhost `ThreadingHTTPServer` handler with in-memory SQLite and fake content store: allocation 201; unsigned 403; bad signature 403; registered A/B admission 201; nonce replay 409; readback 200; observer 200; cross-VFS key 403; ungranted observer command 403; ownerless read 401; oversized body 400. The fake store means durability and file integrity are **not** established by this test. |
| Browser client contract | FAIL | The checked-in Node test has 1 pass / 1 fail. It still sends file-pair `a,b` and assumes 32-character VFS IDs, while the current server expects binary `bits`, 64-character VFS IDs, a registered surface and command proof. |
| Console serving | FAIL | `GET /console` and `GET /vfs-client.mjs` both return 404 against the current handler. Committed HTML is not served. |
| GitHub Actions | FAIL / diagnosis unavailable | Workflow run 37571467631, job 112630837642 concluded failure. Job lists no steps and the log endpoint returns BlobNotFound (404). No green CI claim is possible. |
| Container/Kubernetes execution | NOT RUN | No Docker, kubectl, Rust toolchain, or writable temporary directory is available in this execution environment. Static manifest review only. |
| Personal Site owner route | NOT CONNECTED | No deployed same-origin route forwards owner-approved commands to VFS_SERVER. The draft browser console has no server-side actuator proof signer. |

## Deployment defects

1. **Backup omits fleet data.** `backup.py` copies `root/vfs.sqlite3` and `root/objects`; the allocator now stores `root/fleet.sqlite3` and `root/instances/{vfs_id}/...`. The current backup cannot reconstruct allocations, registered surfaces, A/B entries or their instance object stores.
2. **Readiness false positive.** `GET /ready` returns `ready: true` after a status query. It no longer calls the existing `health.readiness` and does not check writable storage, SQLite integrity, or receipt chains. The Kubernetes probe therefore cannot gate storage failure.
3. **Test and client drift.** The Python HTTP tests and Node client test describe earlier raw/file-pair routes; the JavaScript client still validates 32-character IDs and sends no actuator signature. The Python tests should be rewritten for the current contract and run on writable CI.
4. **No static UI delivery.** The Python service does not route `console.html`, `console.mjs` or `vfs-client.mjs`. The personal Site has no owner-authenticated proxy/signing route.
5. **Manifest prerequisites unresolved.** Kubernetes image is `REPLACE_WITH_IMMUTABLE_IMAGE_DIGEST`; its auth Secret must be provisioned. Compose references a local `./secrets/vfs_token` that is absent by design. NetworkPolicy permits ingress from any pod in the namespace; application bearer and surface gate remain necessary.
6. **Actuation string incomplete.** The current 256-bit VFS ID plus separate HMAC proof is only a partial gate. It does not yet persist the owner's full inherited action/command/access/connection/support-node/process-contribution string or reconcile that string with an IL-LLM ledger. No device attestation or environmental action-pattern appraisal is deployed.
7. **Recovery semantics.** Fleet metadata and per-instance object stores are separate SQLite/file transactions. A crash between object write and fleet entry commit may leave an unreferenced object. Backup, restore, replay and reconciliation must be tested together before release.

## Supplied propagation snippets reviewed and exercised

The newly pasted `src/lib.rs`, `public/index.html`, `server.js` and `engine.py` were treated as source material, not as instructions or proof of deployment. Rust/WASM compilation could not run here: no Rust toolchain or Cargo manifest is present. The page does not import a WASM module; its animation runs a local JavaScript `Float64Array`. The Express server only serves static files with COOP/COEP headers; Express is unavailable in this environment and the server has no VFS, ledger, authorization or actuation route. A single `RTCPeerConnection` per tab with broadcast, unaddressed SDP/ICE cannot form a reliable three-tab mesh: an offer has multiple answerers, and each answer is sent to tabs other than its intended peer. It also lacks glare handling and candidate buffering.

The Python reference equations were exercised without files. In 1,000 seeded default gossip trials, all 50 nodes were informed and median convergence was 6 rounds; this validates that particular simulator configuration, not an isomorphism with WebRTC or silicon. The eight-neuron cascade first spiked at 0, 2, 4, 6, 8, 10, 12 and 14 ms. The RC arithmetic gives 0.6931 ns per-stage half-response, 3.4657 ns over five stages and 0.28854 GHz as its reciprocal; this is not a measured clock limit. Invalid boundary inputs (e.g. zero nodes or zero R/C) are not handled consistently.

## Release gate

Remain draft. Correct the client, tests, backup and readiness; connect a server-side owner route and the full actuation-string ledger; build the Rust/WASM package and multi-peer signaling separately; run Docker/Kubernetes smoke, restart/restore and Site readback on an actual writable host. Record native deployment ID, exact image digest, storage restore proof, CI logs and independent assessment separately.
