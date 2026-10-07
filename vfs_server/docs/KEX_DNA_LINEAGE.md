# KEX DNA first lineage subscription — VFS control contract (draft)

Status: design and falsification contract. This does not assert a live attestation service or an unforgeable physical fingerprint.

## Invariants

- Virtual origin `1` is permanently powered and unaddressable. Graph admission begins `1 > 2`; the 64×64 memory VFS names `[1,1]` the singular apex and `[2,2]` the first payload cell.
- A = 1, B = 0. `AX(X)` and `BX(X)` are reversible binary graph mappings. B = 0 is a valid state, not missing allocation.
- VFS_SERVER allocates a fresh 256-bit random VFS string per admitted system/submission. This is the genesis identifier shared by its VFS and IL-LLM ledger. Its unpredictability comes from a cryptographic random source, not from environmental telemetry. The first lineage subscription binds that identity to an immutable genesis record; later actions append transitions.
- The parent lineage seed digest and child seed digest are distinct. Inheritance is explicit, signed and traceable to the parent admission; possession of a copied digest does not prove possession of a secret.
- No `ACTIVE` or `ATTESTED` claim is produced from a self-reported metric or a storage receipt alone.

## First subscription envelope

```json
{
  "schema": "keddeh.kex-dna.first-lineage.v1",
  "subscription_id": "server-generated",
  "vfs_id": "64-lowercase-hex-CSPRNG-identifier",
  "il_llm_ledger_genesis_id": "same-allocated-vfs-id",
  "parent_lineage_digest": "sha256",
  "child_public_key_fingerprint": "sha256",
  "child_seed_commitment": "sha256",
  "ab_entry_id": "admitted-ab-entry",
  "state_digest": "sha256",
  "environment": {
    "sampling_interval_ms": 297,
    "window_start_monotonic_ns": 0,
    "window_end_monotonic_ns": 0,
    "sample_count": 0,
    "temperature": {"unit": "celsius", "sensor_ids": [], "median": 0, "mad": 0},
    "cpu_load": {"unit": "fraction_of_capacity", "median": 0, "mad": 0},
    "region": {"claim": "coarse-region", "source": "declared-or-verifier-observed"},
    "sample_trace_digest": "sha256"
  },
  "freshness": {"verifier_nonce": "random", "issued_at": "timestamp", "expires_at": "timestamp"},
  "attestation": {"format": "EAT-or-TPM", "evidence_digest": "sha256", "verifier_result_id": "optional"},
  "first_action_graph_digest": "sha256",
  "previous_lineage_digest": null,
  "signature": "child-key-signature-over-canonical-envelope"
}
```

This is a schema illustration, not an API promise. The random VFS string is a public identifier, not a secret authenticator; it must be bound to an authorized key and signed ledger genesis. Store actual sensor samples in a protected VFS object and expose only the trace digest and summaries in a receipt. Capture sensor provenance, units, calibration, timestamps, sample loss, CPU core normalization, thermal throttling, load and operating region. A region claim must identify its source; a network address is not proof of physical location. A median alone loses temporal behavior, so retain the bounded trace, robust spread (MAD), and acquisition timing.

## Subscription state machine

1. `ALLOCATED`: the VFS and quota exist.
2. `CHALLENGED`: the verifier issues a one-use nonce and bounded sampling window.
3. `PENDING_EVIDENCE`: A/B state, parent relation, environmental trace and signed genesis envelope are persisted with an actor receipt.
4. `OBSERVED`: an independent readback reconstructs the A/B state and validates all stored digests and receipt-chain continuity.
5. `CLAIMED` or `ATTESTED`: an independent verifier appraises freshness, key provenance, measured software, sensor context and externally corroborated actuator evidence. Only a successful policy result may yield `ATTESTED`.
6. `ACTIVE`: an authorized lineage policy admits the first subscription. Every later action links `previous_lineage_digest`, sequence, and signed transition in both the VFS and IL-LLM ledger; migration and re-anchoring are explicit events.

Implement admission idempotently by `subscription_id` and a unique first-subscription key for the allocated VFS. The actor write and registry promotion span separate stores in the current prototype; a journaled pending state and recovery/readback are required before claiming atomicity. A failed or stale challenge must not consume a lineage identity.

## Action and actuation pattern lineage

The match target is the **causal action graph**, not equality of sensor numbers. Each event records: the authorized instruction and policy revision; actor and actuator identities; operation type; target namespace; input commitment; A/B graph projection; predecessor event digest; result and externally observed post-state digest; monotonic timing and the environmental context window. The VFS persists the bytes and receipt chain; the IL-LLM ledger binds the same genesis identifier to semantic action relations and their evidence references. The two ledgers must reconcile by event ID and digest before a lineage transition is marked observed.

A pattern comparator should normalize expected differences (timestamps, generated IDs, target-specific paths) while preserving action order, causal dependencies, actuator choices, outcome transitions and timing distributions. Compare rolling event subgraphs and response to fresh, bounded challenges. Version the canonicalizer and comparator, then measure false accepts, false rejects and drift under thermal/load and regional changes. Matching a historical pattern is evidence of continuity only if the actuations and post-states are independently observed and bound to a device-held signing key; a script can otherwise imitate the same action sequence.

## Authenticity claim and threat tests

Environmental measurements are **context for action patterns**, not the matching identity or a cryptographic secret. Identical or replayed temperature/load/region samples can be submitted by software controlling the sensor API. Quantization and medians further reduce distinguishable information. Signing a report authenticates the reporting key; it does not automatically prove that the reported sensor data are genuine or recent. A device-held non-exportable key, verified measured environment, fresh nonce, and independent appraisal establish a stronger claim under the attestation platform's stated trust assumptions.

Before describing KEX DNA as unforgeable, test: (a) replay of an old median and whole trace under a fresh challenge; (b) same-region, same-model sibling devices under matched workloads; (c) VM and sensor API substitution; (d) fan, heater, power-limit and load manipulation; (e) region proxy or migration; (f) copied VFS and child seed commitment; (g) reboot/thermal drift; (h) clock skew and `0.297`-second phase collision after 33 hours. Record false accept and false reject rates, confidence intervals, enrollment latency, storage overhead and work per verification.

`0.297` seconds is a scheduling interval in this contract, separate from any `0.297` angular-frequency parameter in the Kuramoto model. Hourly boundaries traverse 33 tick phases and realign at 33 hours exactly. A shared start phase still collides; worker identity, independent phase assignment, bounded jitter and load coordination remain necessary.

## References

- RFC 9334: attester, verifier, relying party, freshness and appraisal roles; a nonce proves signing after challenge, not necessarily that an earlier sensor reading is recent.
- RFC 9711: EAT claims, environmental/location characteristics, claim age and trustworthiness vary with the attester implementation and verifier.
- RFC 9683: TPM-backed integrity verification does not itself verify geographic location.
- Keddeh source: `KEDDEH_64x64_MEMORY_VFS.json` apex, first payload cell and allocated-unbound state law; user correction in this thread for A/B and first lineage subscription.
