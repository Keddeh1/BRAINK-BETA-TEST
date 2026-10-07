# Compute and optionally actuate propagation

## Function and architectural application

Accept directed adjacency, optional initial values, steps 1–1000 and boolean actuate. Compute the common software model; optional output mapping clamps to [0,1] and rounds to uint32 across declared R36 registers.

## User guidelines

Read model state and actor receipts. Multi-register execution retains a valid prefix and is not a single atomic hardware transaction.

## Entry and expected context

`cloud propagate | cloud enact`

## Fit, case and field use

Explore a directed topology, then explicitly project its software result into admitted register actuation.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
