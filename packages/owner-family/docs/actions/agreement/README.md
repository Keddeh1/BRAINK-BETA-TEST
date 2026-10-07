# Review, accept or revoke projection service permission

## Function and architectural application

Return purpose, data handling, retention, withdrawal, execution scope and principal; persist versioned owner-space acceptance or revocation.

## User guidelines

Read terms before accepting. Customer registration grants no runtime authority. Revocation blocks projected mutations; disconnect additionally fences the family actor pipeline.

## Entry and expected context

`POST /api/web4/control {action: agreement, version: 1.0, accepted: true}`

## Fit, case and field use

An authenticated owner explicitly chooses service permissions without an invented legal contract.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
