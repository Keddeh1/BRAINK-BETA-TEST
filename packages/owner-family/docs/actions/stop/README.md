# Stop the host controller cleanly

## Function and architectural application

Stop owned host subprocess groups and wait for the controller root lock to release. Docker domain families retain their separately supervised persistent state and restart policy.

## User guidelines

Preserve journals and keys; this is a lifecycle operation, not state deletion. Stop domain containers separately only through an explicit owned-domain maintenance procedure.

## Entry and expected context

`python -m keddeh_namespace.web4_runtime stop --root /private/family`

## Fit, case and field use

Perform a controller upgrade while the retained domain state remains available for rehydration.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
