# Data, file attribution and lineage contract

## Identities and evidence paths

| Record | Identity/version | Attribution and validation | Limits |
|---|---|---|---|
| Owner original | SHA-256 and original filename | Local Library and private queue exact-byte comparison; ten launch inputs plus four control/HCI inputs | Custody hash is not an authorship or license adjudication |
| Derived launch source | Relative path and SHA-256 | `verify_launch`; derivation metadata; originals retained separately | Source transformations must remain distinguishable from originals |
| Qualified executable | Full Git commit plus file hash manifest | `.keddeh/EXECUTABLE_MANIFEST.json`; guard before launch | Later documentation commits may share a qualified executable base |
| Wheel | Version, bytes and SHA-256 | Clean build, isolated installation and tests | Version alone is insufficient identity |
| Controller image | Content-addressed local image ID; pinned base digests | Wheel/dependency hashes, Docker-client hash, installed-image tests | Local image identity is not a remotely published registry release |
| Family | Repository identity and family ID | Manifest, private root, port offset and exact owner label | Separate roots are not independent physical hosts |
| Actor transaction | Tenant/node/nonce and journal receipt | R36 durable journal and detached readback verification | Whole multi-register cycle is not a single atomic commit |
| Namespace generation | Signed envelope, stateRoot, phaseRoot, parent digest | Ed25519 trust roles, exact data roots and registry replay | Local generator/controller does not become an independent assessor |
| VFS artifact | Digest, path and predecessor | Actor admission, exact-byte GET, observer receipt and history verification | Native observer is a separate local role, not external assurance |
| Subscription | Family subscriber, prefix and monotonic cursor | Hash-verified immutable object before acknowledgement | Downloaded artifacts do not authorize execution |
| Service permission | Owner space, agreement version, principal and timestamp | Private durable acceptance/revocation and request context | Operational record, not a legal contract or public-customer token |
| Pipeline fence | Connected state, generation and reason | Durable save before acknowledgement; stale-generation rejection | Selected-family software admission only |
| Controlled document | Stable document ID, revision and SHA-256 | Front matter and controlled register integrity validator | Technical issuance is separate from independent approval |
| Research result | Step number, digest and versioned evidence path | VFS actor/readback, actual R36 transaction and signed detached observer | Results and recorded limitations must survive later iterations |

## Attribution rules

Every original retains its exact filename and byte hash. Record supplied author
metadata as supplied; do not convert a filename or owner account into a legal
ownership assertion. Keep third-party dependencies and their license metadata in
the release inventory. Separate owner original, extracted fragment, adapted launch
source, generated document, installed runtime and observed result.

Use full Git commit IDs for executable baselines; use branch names only as working
locations. Runtime fingerprints bind active code and external service bindings.
Each result must identify scope, generator, observer, command, exit/outcome and
limitations. Signatures establish key-bound content integrity under the configured
trust policy; they do not alone establish inventor identity or assessor independence.

Public repositories carry permitted metadata and qualified software artifacts.
Private originals/bundles remain in private repositories and owner VFS. Credentials,
keys, customer records and mutable operational state are not release members.
A redacted/public derivative receives its own digest and a reference to private
custody, rather than pretending to be the original.

## Serialization and compatibility

Existing owner protocols retain their field names and schemas. Adapters do not
rename original R36/MCP fields merely to match a new style. Package metadata uses
explicit schema/version markers where implemented; legacy documents may use
`schema_version`. Signed namespace observations use canonical serialization and
an exact float64 representation before hashing. Runtime phase files use ordinary
JSON numbers and must not be confused with signed canonical envelope encoding.

A breaking schema change requires a migration/compatibility decision, test evidence,
new version and rollback plan. Preserve old receipts and source artifacts. Do not
rewrite historical evidence into a new schema without a separately identified
conversion record.

## Data lifecycle and user space

Owner telemetry, secrets and agreements are private operational data. Customer
interest records have their separate existing consent and 90-day retention behavior.
The architecture does not authorize transferring either class to an arbitrary
off-site destination. Record purpose, recipients, location, retention, withdrawal
and deletion/hold authority before enabling a transfer. Global policy retention
periods are internal defaults requiring owner obligation review; not every store
currently automates those periods.

Owner-only bearer tokens are not general user-space/tenant credentials. The
projection agreement enforces the owner space and current version; customer
registration grants no owner authority. A multi-tenant service needs separately
scoped identities, authorization, isolation and access-review evidence before use.
