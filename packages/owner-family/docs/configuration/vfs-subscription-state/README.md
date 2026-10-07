# vfs-subscription-state

## Configuration fields

`cursor, objects, published_digest, actor_receipt, observer_receipt, status, error`

## Function and architectural application

Cursor advances only after a processed event is durable. Package bytes are hash-verified in a private content-addressed mirror. Subscription progress is acknowledged by VFS_SERVER.

## Guidelines, fit and field use

Use this contract when commissioning, qualifying or recovering an owner family. Match its values to the selected repository and actual host bindings; retain predecessor state and verify readbacks after changes.

## Supporting documents

See the family manifest, OWNER_ENVIRONMENT.md, package README and corresponding process/action contracts.
