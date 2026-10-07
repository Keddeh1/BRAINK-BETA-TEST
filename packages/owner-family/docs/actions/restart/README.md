# Recover an owned service

## Function and architectural application

Restart only a service declared in the supervisor specification. Process-group cleanup includes child workers; stdio MCP is reinitialized. Restart requests return PIDs and require health readback.

## User guidelines

Select an existing owned service name. Automatic recovery applies to all managed roles with bounded retry rate.

## Entry and expected context

`cloud restart node-19100`

## Fit, case and field use

Recover an exited workstation, broker, agent or actuator without adopting a foreign process.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
