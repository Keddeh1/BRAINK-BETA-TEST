# process-envelope

## Configuration fields

`RLIMIT_CORE/NOFILE/FSIZE, restart backoff, Docker memory/cpus/pids-limit/cap-drop/read-only`

## Function and architectural application

Host children disable core dumps and bound descriptors/output. Domain containers additionally use 256MiB memory,0.5 CPU,64 processes,32MiB Node heaps,16MiB probe heap,read-only code,no added Linux capabilities and explicit state mounts.

## Guidelines, fit and field use

Use this contract when commissioning, qualifying or recovering an owner family. Match its values to the selected repository and actual host bindings; retain predecessor state and verify readbacks after changes.

## Supporting documents

See the family manifest, OWNER_ENVIRONMENT.md, package README and corresponding process/action contracts.
