# bilateral-state

## Configuration fields

`enabled, cycle, pending, last, phase, status, error`

## Function and architectural application

Durable enabled intent, partially returned register prefix and owner software PLL vector. Explicit pause preserves intent; restart does not silently reset a phase or register transaction.

## Guidelines, fit and field use

Use this contract when commissioning, qualifying or recovering an owner family. Match its values to the selected repository and actual host bindings; retain predecessor state and verify readbacks after changes.

## Supporting documents

See the family manifest, OWNER_ENVIRONMENT.md, package README and corresponding process/action contracts.
