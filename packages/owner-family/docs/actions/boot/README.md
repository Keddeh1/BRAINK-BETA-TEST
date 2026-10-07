# Execute broker/agent substrate boot

## Function and architectural application

Queue the supplied six-phase BOOT_SUBSTRATE command; preserve any queued/leased command rather than overwriting it. The paired outbound agent returns bound readbacks.

## User guidelines

Use when the owner requests boot lifecycle execution; read current boot completion before a second command.

## Entry and expected context

`cloud boot`

## Fit, case and field use

The owner re-evaluates mount, targets, writable state and capabilities through the supplied runtime.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
