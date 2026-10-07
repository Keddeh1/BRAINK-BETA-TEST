# http-worker: Original Python core execution worker

## Function and architectural application

Source/entry: `braink_core_runtime.py`.

## Configuration and inputs

Harness stdio and per-family journal file.

## Readback and attribution

Deterministic register receipt recovered from durable bytes. Source custody and active runtime fingerprints identify the actual execution.

## Fit, case and field use

Worker child shares its owned process group and is cleaned up on harness restart.

## Operator guidelines

Read actual health after launch/recovery, retain state and credentials, and use the owning family supervisor. Actor results and independent production assessment are different evidence scopes.
