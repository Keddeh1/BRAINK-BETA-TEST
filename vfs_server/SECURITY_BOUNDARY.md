# VFS HTTP security boundary — review required

This patch fixes three source-level defects: an accidental literal `\\n` in Python import lines, an uninitialized `Handler.authorizer`, and missing authorization in `do_POST` for artifact writes and verification.

## Startup
- Production or non-development: `python -m vfs_server.server --token-file /path/to/secret --host 127.0.0.1`.
- Local development only: `--insecure-local-dev` must be explicitly selected and is rejected for non-loopback binding.
- Without either configuration the service fails closed before accepting requests.
- `/status` and `/ready` remain unauthenticated metadata endpoints. Review their exposure at ingress.

## What this does not establish
Bearer-token equality is a coarse admission gate, not actor-specific authority, per-operation scope, expected state-version compare-and-swap, lease ownership, anti-replay, or an independent verifier. Those remain necessary before describing VFS as an end-to-end BRAINK-authorized external mutation boundary.

## Deployment review
This is a breaking security change for any existing deployment that depended on no-token behavior. Review the actual host configuration and secret custody before merge. Do not log the bearer token. Require TLS and a protected ingress when used beyond loopback. Run the unit and HTTP integration tests and verify no unauthenticated target mutation occurs.
