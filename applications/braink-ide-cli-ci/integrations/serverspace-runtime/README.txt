ServerSpace additive substrate runtime

The supplied mining_engine/stratum_engine.py is retained byte-for-byte with archive/member SHA256 provenance. The missing substrate implementation was developed here; it is not claimed to be a discovered existing daemon. The prior ServerSpace node and its global service configuration were preserved.

Persistent mmap backing and canonical_state.dat reside under /workspace/braink-setup/families/SERVERSPACE/runtime/substrate-primary and substrate-replica. Each has its own identity, daemon ownership lock, publisher process, canonical-writer process, UDS readiness.sock and independently allocated loopback API listener. The daemon monitors worker liveness and stops readiness and its API when a worker exits. Shared state uses POSIX file locking and fsync; no lock-free hardware or power-loss guarantee is asserted.

Frame: big-endian >4sII32sI header, magic KXS1, readiness mask, payload length, SHA256 payload digest, CRC32 over the header prefix and payload, followed by complete canonical JSON. Mask 7 is supplied only with a fresh publisher proposal and a writer committing state under the active daemon; the serving watchdog independently checks both actual worker process identities/liveness. The client checks SO_PEERCRED against the expected daemon PID and local UID, exact frame length, CRC32, SHA256, identity, freshness and both worker-ready fields.

The publisher and canonical writer are the two substrate workers. They are not asserted to be two mining pool workers. The mining API starts through the real UDS handshake and checks readiness for every read. /api/substrate returns the actual frame observation; /api/telemetry includes the retained mining client's actual DISCONNECTED state. No external pool is configured. Source defaults for difficulty and efficiency are returned as null rather than measurements. Simulated firmware actions and the global-install bootstrap were not executed.

Qualified worker-failure test: terminate the owned primary publisher; confirm readiness closes; confirm replica remains ready; wait for daemon ownership cleanup; restart primary; confirm its mmap inode is preserved and fresh readiness returns. Only these newly created instance processes were restarted.

CLI:
python substrate.py --root /path/to/runtime --identity NODE_ID daemon
python substrate.py --root /path/to/runtime --identity NODE_ID verify

Website route /serverspace/substrate publishes a labelled recorded execution snapshot. It is not a live public connection to loopback APIs. Original Site identity, audience and owner checks are preserved. Build/publication status is retained separately in website-publication.json after the native deployment result.
