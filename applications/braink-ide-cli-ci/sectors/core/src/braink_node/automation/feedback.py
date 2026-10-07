from braink_node.protocol.catalogue import digest


def run(context):
    instances = context.deployment()['instances']
    if len(instances) < 2:
        return {'state': 'AWAITING_INSTANCES', 'exchanges': []}
    sender, recipient = instances[0]['instance'], instances[1]['instance']
    evidence = [context.latest(target) for target in ('reconciliation', 'continuity', 'diagnostics')]
    rows = [row for row in evidence if row]
    anchor = {'type': 'RELATIONAL_ANCHOR', 'source': sender, 'definition': context.catalogue()['definition_sha256'],
              'relation': {'operation': 'architecture-maintenance-observation', 'evidence': [row['artifact_digest'] for row in rows]},
              'uncertainty': [row['target'] for row in rows if row.get('state') not in ('ALIGNED', 'CONTINUOUS', 'OBSERVED')],
              'contradiction': [finding for row in rows for finding in row.get('findings', [])], 'next_route': 'module://braink_node.automation.development/run'}
    import importlib.util
    import hashlib
    from pathlib import Path
    lexical = Path(context.config['owner_export']).parent / 'lexical_compiler.py'
    spec = importlib.util.spec_from_file_location('braink_owner_feedback_calibration', lexical)
    owner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(owner)
    calibration = owner.observer_calibrate(sender, 'architecture_observed', recipient, context=anchor)
    anchor['relation']['calibration'] = calibration
    anchor['relation']['calibration_source_sha256'] = hashlib.sha256(lexical.read_bytes()).hexdigest()
    identity = {'sender': sender, 'recipient': recipient, 'anchor': anchor}
    def execute(key):
        return context.mesh.request('/exchange', {'sender': sender, 'recipient': recipient, 'row': anchor, 'message_id': key})
    exchange = context.action('feedback', identity, execute)
    inbox = context.mesh.request('/inbox', {'instance': recipient, 'after': exchange['result']['sequence'] - 1})
    if not any(row['digest'] == exchange['result']['digest'] and row['document']['row'] == anchor for row in inbox):
        raise RuntimeError('Feedback inbox readback differs')
    return {'state': 'DELIVERED', 'sender': sender, 'recipient': recipient, 'exchange': exchange, 'owner_contract': 'RELATIONAL_ANCHOR', 'owner_observer_calibration': calibration,
            'learning_execution': 'Not inferred from message delivery; existing owner learning routes retain their own evidence.'}
