BRAINK Web4 admission sector

The supplied scaffold is preserved as a separate additive module. Its 116-byte frame consists of a 52-byte signed context and 64-byte signature. The four architecture bytes come from the architecture authority; this module assigns none.

Required adapters: actual Web4 exchange; pinned Ed25519 verification; native KEX validation; authoritative IL-LLM ledger. No production adapter is connected by this delivery. Local tests use explicitly labelled test doubles and establish no cryptographic, transport, or durability guarantee. The user-reported 12 tests were not supplied and are not counted as reproduced results.

Ledger admission contract: accept(expected_floor, epoch, wire, payload) must check the authoritative floor and persist frame, payload, validation evidence, and epoch in one atomic transaction. Independent runtime locks do not prevent concurrent ledger writers; the ledger must enforce compare-and-commit itself.

Integration issue: the supplied four-argument accept interface does not carry validation evidence explicitly. Before production binding, the native adapters must establish a request-scoped evidence handoff or an agreed explicit evidence argument. Do not infer evidence from a successful boolean. Do not replace the native ledger with a synthetic ledger.

Commit exceptions or missing receipts leave persistence outcome uncertain. The scaffold remains HALTED; reconciliation must inspect the authoritative ledger before a new runtime is admitted. No automatic reset or retry is provided.

Hardware isolation, redundancy, real-time guarantees, dual authorization, certification, FROST, and pBFT remain unqualified integration requirements.

Local check: python -m unittest discover -s applications/braink-ide-cli-ci/sectors/admission -v
