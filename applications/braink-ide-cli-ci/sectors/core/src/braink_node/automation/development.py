from braink_node.canonical import canonical_bytes
from braink_node.protocol.catalogue import digest
from braink_node.storage import atomic_write


def run(context):
    reconciliation = context.latest('reconciliation')
    evolution = context.latest('evolution')
    diagnostics = context.latest('diagnostics')
    delivery = context.latest('delivery')
    tasks = []
    for target in ('ceremonies', 'reconciliation', 'continuity', 'feedback', 'delivery', 'diagnostics', 'placement', 'recovery'):
        observation = context.latest(target)
        if observation is None or observation.get('state') in {'EXECUTION_ERROR', 'RETRY_REQUIRED', 'DISCREPANCIES', 'FAILURES_OBSERVED', 'AWAITING_BUILD_RESULTS'}:
            tasks.append({'id': digest({'target': target, 'evidence': (observation or {}).get('artifact_digest')}), 'source': (observation or {}).get('artifact_digest'),
                          'implementation_route': 'module://braink_node.automation.' + target + '/run', 'state': 'OPEN' if target != 'delivery' else 'AWAITING_QUALIFICATION'})
    for finding in (reconciliation or {}).get('findings', []):
        kind = finding['kind']
        route = 'module://braink_node.automation.ceremonies/run' if kind in {'REVISION_NOT_DEPLOYED', 'CEREMONY_INTERRUPTED'} else 'module://braink_node.automation.diagnostics/run'
        tasks.append({'id': digest(finding), 'source': finding, 'implementation_route': route, 'state': 'OPEN'})
    for failure in (diagnostics or {}).get('failures', []):
        tasks.append({'id': digest(failure), 'source': failure, 'implementation_route': 'module://braink_node.automation.diagnostics/run', 'state': 'OPEN'})
    if evolution and evolution.get('changed_modules'):
        tasks.append({'id': digest({'revision': evolution['catalogue_sha256']}), 'source': evolution['artifact_digest'],
                      'implementation_route': 'module://braink_node.automation.delivery/run', 'state': 'QUALIFIED' if delivery and delivery['state'] == 'QUALIFIED' else 'AWAITING_QUALIFICATION'})
    cycle = {'state': 'VERIFIED' if not tasks or all(row['state'] == 'QUALIFIED' for row in tasks) else 'WORK_DERIVED',
             'tasks': tasks, 'catalogue_sha256': context.catalogue()['definition_sha256'],
             'routes': ['source-evolution', 'clean-sector-build', 'instance-delivery', 'independent-readback', 'relational-feedback'],
             'novel_source_generation': 'Requires an actual owner development route; this module does not fabricate generated engineering.'}
    atomic_write(context.root / 'development-frontier.json', canonical_bytes(cycle))
    return cycle
