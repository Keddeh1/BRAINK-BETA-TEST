# Run the owner supervisor

## Function and architectural application

The detached controller owns process groups, authenticated gateway, bilateral governor, domain resumption and VFS polling. This foreground entry is normally invoked by start.

## User guidelines

Use under an approved Linux process manager; only one controller may hold the root lock.

## Entry and expected context

`python -m keddeh_namespace.web4_runtime serve --root /private/family`

## Fit, case and field use

A cloud instance runs a persistent family from its own configuration and keys.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
