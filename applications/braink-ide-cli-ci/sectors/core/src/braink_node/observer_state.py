"""Shared I/O/q/t context across domains. Zero values never erase identity."""
from braink_node.canonical import canonical_bytes


def observation(identity, origin, value, at, domain):
    if not isinstance(identity, str) or not identity:
        raise ValueError('Observation requires the actual entity identity')
    if origin is None or at is None or not isinstance(domain, str) or not domain:
        raise ValueError('Origin, temporal context and domain are required')
    state = {'I': identity, 'O': origin, 'q': value, 't': at, 'domain': domain}
    # Validate capture without treating zero, False, empty collections or None as no entity.
    canonical_bytes(state)
    return state
