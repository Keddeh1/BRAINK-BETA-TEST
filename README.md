# BRAINK - KEX_SEED Ring Architecture Bootstrap

This repository bootstraps work for implementing the KEX_SEED Ring Architecture (Ring 0..3) and the Domain/Runtime Engines described in the provided architecture notes.

Files added by the bootstrap:

- ARCHITECTURE.md    — full architecture and deep dives (source content provided)
- sims/ring1_sim.py   — Python validation simulation skeleton for Ring 1 invalid-access scenario
- docs/TODO.md       — next steps and implementation checklist
- requirements.txt   — minimal Python requirements
- .gitignore         — python ignores
- LICENSE            — MIT License

See ARCHITECTURE.md for the original specification and deep-dive text.

## Persistent owner-runtime deployment

This repository now carries a pinned, running owner-runtime family. See [.keddeh/README.md](.keddeh/README.md) for launch, state retention, VFS subscription and operating scope; [deployment readbacks](.keddeh/deployment-evidence.json) identify the actual engine and cached package digest. The [distributed package](packages/owner-family/README.md) includes its wheel, qualification result and per-process/action/configuration guides. Customer-frontage publication and independent production assessment remain separate from this cloud-host deployment.
