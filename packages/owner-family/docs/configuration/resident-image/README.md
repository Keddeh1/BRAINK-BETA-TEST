# resident-image

## Configuration fields

`image_id, qualified_commit, qualified_wheel_sha256, docker_cli_sha256, python_base, node_base`

## Function and architectural application

Content-addressed local image and verified wheel/dependency hashes; 1GiB/one CPU/256 PIDs per trusted owner controller. Named UID 1000 account, no HOME reassignment. Build and qualify on a new host before claiming restoration.

## Guidelines, fit and field use

Use this contract when commissioning, qualifying or recovering an owner family. Match its values to the selected repository and actual host bindings; retain predecessor state and verify readbacks after changes.

## Supporting documents

See the family manifest, OWNER_ENVIRONMENT.md, package README and corresponding process/action contracts.
