Shared KEDDEH HCI sector

This delivery implements the supplied seven domain surfaces and terminal A/M/X controls as an additive sector. Data comes from the caller's readback, not fixed seed, peer, certification, saturation, integrity or convergence assertions. Surface controls describe intent; rendering never executes them. Local trace digests are correlation records, not signed evidence or authoritative ledger commits.

The panel connects to the existing native colony using --native-root. It reads each actual VFS definition, compares the retained definition artifact and identity with the deployment manifest, and verifies the native receipt chain. Hardware fields remain NOT_OBSERVED; this adapter does not infer hardware health from VFS custody. A/B staging and MRAM compaction require actual native action adapters. Exceptions display OUTCOME_UNKNOWN and are never retried automatically. Enter submission does not guarantee action idempotency; the adapter must use the native request/receipt protocol.

The render path uses 83 ASCII columns, wraps long fields, escapes terminal controls, and emits append-only text. It does not launch a shell to clear the screen. The layout audit is a structural check, not an ISO-prescribed width or proof of WCAG/ISO compliance. Terminal contrast depends on the user's terminal configuration. Screen-reader, usability, and quality assessments remain required.

physical-layout.json records the supplied /mnt/KEX_BOOT and /mnt/KEX_RUNTIME map and explicitly identifies missing owner-provisioned/native files. Both slot bin directories receive the shared core and diagnostics panel. The clean HCI package contains those actual files only; it does not supply fake bootloaders, entropy keys, FROST signatures, hardware mappings or ledger contents. FAT32 alone cannot establish immutable boot code. A directory alone cannot establish a hardware memory-backed ephemeral ring. Physical SD-card flashing, boot qualification, power-loss behavior, and node rehydration have not been verified.

Checks:
python -m unittest discover -s applications/braink-ide-cli-ci/sectors/hci -v
python applications/braink-ide-cli-ci/sectors/hci/kex_diagnostics_panel.py --test-automated-audit

Native readback requires the existing braink-node-core installation:
python applications/braink-ide-cli-ci/sectors/hci/kex_diagnostics_panel.py --native-root /path/to/native/colony

Clean additive package:
python applications/braink-ide-cli-ci/sectors/hci/build_sector.py --output /path/to/hci-slots.zip

Runtime interaction checks require the existing braink-node-core installation. The 12-test suite includes 32 concurrent submissions of the same request identity through native execute/dispatch, distinct identities, serial action/exit behavior, and 32 frames during 64 writes in an isolated native VFS. The provider is an explicitly labelled localhost HTTP fixture. This does not bind slot swap or compaction, establish distributed idempotency, or verify Triad of Triads topology. The native lock is host/filesystem scoped. The viewport check measures frame width; it does not emulate a physical terminal. A fixed 83-column frame exceeds a 40- or 80-column viewport.
