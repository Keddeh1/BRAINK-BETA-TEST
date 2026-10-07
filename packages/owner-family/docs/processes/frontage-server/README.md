# frontage-server: customer pages and registration

## Function and architectural application

`keddeh_namespace.frontage_service` serves the declared customer HTML routes and same-origin public runtime/evidence readbacks. It runs as an owned managed process in the keddeh.com family. Public customers remain outside the authenticated owner actuator boundary.

## Configuration and inputs

The family `frontage` configuration supplies source_root and port. The supervisor supplies a private state directory and current sanitized runtime status. Static routes are declared in route-manifest.json; scripts/styles stay same-origin under a restrictive CSP.

## Customer functions and guidelines

Navigation opens each relevant product, architecture, research, evidence, developer, enterprise, contact, interest and privacy page. The evidence button requests actual sanitized runtime readbacks. The developer download returns the qualified wheel. Contact/interest forms require name, valid email, topic, message and explicit consent; organisation is optional. A successful submission returns its durable reference, without sending email or creating an account. Repeat identical request identities return the same receipt; conflicting payloads are rejected. Private registrations are retained for 90 days and are never committed to Git.

## Fit, case and field use

Use this process for an evidence-attributed evaluation frontage, research interest registration and technical customer qualification. Customer-facing claims are scoped in claims.json. The service is locally qualified on one cloud host; native Site publication, public TLS, independent production assessment and commercial commitments require their own returned evidence.

## Supporting documents and validation

See the keddeh.com frontage README, route-manifest.json, CONTROL_REGISTER.json, DOM_EVIDENCE.json and tests/test_frontage.py. DOM tests cover all 13 routes and their internal links, mobile/keyboard navigation and both forms; HTTP tests cover consent, durable idempotency, restart, conflicts and foreign origins.
