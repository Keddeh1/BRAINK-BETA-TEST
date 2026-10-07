# Admit exact owner sources

## Function and architectural application

Create a fresh private root from the library manifest and configured port offset. Existing nonempty roots are rejected.

## User guidelines

Use once when commissioning a new family; compare admitted source hashes before activation.

## Entry and expected context

`python -m keddeh_namespace.web4_runtime prepare --root /private/new-family --library /private/library/manifest.json`

## Fit, case and field use

An operator provisions a repository family without overwriting an existing journal.

## Supporting source and evidence

See `src/keddeh_namespace/web4_runtime.py`, the owner source manifest, process contracts and full qualification logs. The gateway accepts authenticated owner actions; customer frontage has a separate access boundary.
