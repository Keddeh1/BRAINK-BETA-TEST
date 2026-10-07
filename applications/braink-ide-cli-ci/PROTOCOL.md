# BRAINK development deployment protocol

Version 1.0 · Implementation and qualification record · Keddeh Systems

Engineering requirements: the owner's supplied BRAINK baselines and explicit function-module, module-family variant, variant-colony, per-instance VFS and IL-LLM subscription requirements. Implementation contribution: Codex. Rights reserved; this document does not confer ownership or licensing of the source systems. No external architecture approval is asserted.

## Independently addressed units

A function module has a stable URI, complete signature, lexical scope, source identity, source-file SHA-256, function-body SHA-256 and definition SHA-256. Python functions, methods, nested functions, lambdas and browser JavaScript functions are enumerated. Browser parsing uses the actual Acorn parser supplied by Node 24, rather than textual function matching. Supporting delivery, qualification and uploaded baseline functions have a separate inventory with their roles and original source.

A module family retains the complete source compilation unit. Function fragments are reference artifacts; decorators, receivers, imports and lexical closures remain in the original family implementation. A family variant records its family/module membership and explicit core dependency edges. A variant colony records its variant membership. Each of the core, CLI, IDE and CI sectors has an independently built wheel and its own colony artifact package. Shared core code retains its original identity while each occurrence receives its own instance.

`FunctionBindings` invokes original Python callables. Bound methods retain their actual receiver; closures retain actual lexical captures. Distinct captures require distinct binding contexts. Source changes or mismatched lambda positions produce an explicit binding error. Browser functions retain their browser realm and event/DOM context; Python invocation does not substitute for a browser execution context.

## Instance lifecycle and ceremony

The instance ID is derived from its definition hash and occurrence path through colony, variant, family and module. An instance directory contains its own VFS objects, SQLite state, receipt chain, ceremony journal and lock. A common parent directory is storage placement, not shared VFS state.

1. Declare the definition and occurrence.
2. Instantiate the byte-preserved owner VFS implementation; write the definition and obtain actor and observer receipts.
3. Register the instance's subscription with the existing owner VFS hub. Read back its own prefix and cursor. Preserve the hub's native cursor and prefix rules.
4. Register an IL-LLM network mesh subscription. Read back the definition identity and owner canonical state evidence.
5. Publish the ceremony through the owner VFS service and independently read back the exact bytes. Verify the instance VFS receipt chain.

A failed operation retains the last completed stage. Restart resumes the same identity and storage. A ceremony is recorded as READBACK only after the actual service operations succeed. The ceremony is an execution protocol, not a new approval process.

## IL-LLM network participation

The deployment mesh calls the owner's existing `il_llm_export()` implementation and preserves the `braink.il-llm.canonical-state.v1` rows, their source evidence and truth descriptions. The export source and resulting state are separately hashed. Subscription registration is durable, authenticated over the configured owner runtime transport, and refuses redefinition of an existing instance identity.

Network exchange uses the existing governance `RELATIONAL_ANCHOR` fields: source, definition, relation, uncertainty, contradiction and next_route. Actual messages receive VFS actor/observer receipts and an ordered recipient inbox. The inbox survives reopening the mesh store. This delivery implementation binds canonical state and relational network exchange; it does not assert that inventory presence proves learning, model inference, or every capability of the wider owner architecture.

## Executable interfaces

- `braink-node protocol catalogue --source <application>` produces the complete runtime function/family/variant/colony catalogue.
- `braink-node protocol mesh --owner-export <owner capability_broker.py> --mesh-token-file <private credential>` runs the network subscription and exchange service.
- `braink-node protocol deploy --source <application> --vfs-token-file <existing hub credential> --mesh-token-file <private credential>` deploys the instances and runs their ceremonies.
- `scripts/build_sector.py` makes fresh sector staging trees, builds the separate wheels, and packages modules, source families, variants, colonies and their wheel references.
- The existing website CLI submits these same operations through the owner's CI queue. Credentials remain in runtime files; artifacts and source never contain them.

## Evidence and qualification

The owner VFS provenance is in `integrations/vfs-source.json`; deployment readback evidence is in `integrations/protocol-qualification.json`. The specification, code, clean build artifacts, deployed state and qualification results have distinct identities.

`tests/test_protocol.py` covers interrupted ceremony recovery, instance separation, restarted subscription and inbox storage, actual network exchange, incorrect credentials, conflicting identities, catalogue determinism and real receiver/closure/lambda binding. The existing core/CLI/IDE/CI qualification remains part of the clean installed-wheel run. Host and website readback observations are reported separately from these tests.

Current deployment scope is the connected Keddeh runtime. Permanent server bootstrap and recovery after destruction of that host require evidence from that host's lifecycle; process restart evidence does not establish those properties.
