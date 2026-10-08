from pathlib import Path
from braink_node.storage import atomic_write
from braink_node.canonical import canonical_bytes
from braink_node.protocol.transport import JSONTransport
from .hosts import capacity


def run(context):
    local = capacity(context)
    candidates = [(local, None)]
    observations = []
    for host in context.config.get('hosts', []):
        transport = JSONTransport(host['endpoint'], Path(host['token_file']).read_text().strip(), timeout=None)
        try:
            observed = transport.request('/capacity', {})
            observations.append(observed)
            if observed['catalogue_sha256'] == context.catalogue()['definition_sha256']:
                candidates.append((observed, transport))
        except Exception as error:
            observations.append({'endpoint': host['endpoint'], 'state': 'OBSERVATION_FAILED', 'exception': type(error).__name__, 'reason': str(error)})
    selected, transport = min(candidates, key=lambda row: row[0]['load'][0] / row[0]['cpus_available'])
    assignments = []
    for colony in context.catalogue()['colonies']:
        if transport is not None:
            identity = {'host': selected['host_id'], 'colony': colony['id'], 'revision': context.catalogue()['definition_sha256']}
            def place(key):
                return transport.request('/place', {'sector': colony['sector'], 'catalogue_sha256': context.catalogue()['definition_sha256']})
            result = context.action('place-colony', identity, place)
            assignments.append({'colony': colony['id'], 'host': selected['host_id'], 'readback': result})
        else:
            actual = [row for row in context.deployment()['instances'] if row['occurrence'][0] == colony['id']]
            if not actual or any(not (context.state / 'instances' / row['instance'] / 'vfs').is_dir() for row in actual):
                raise RuntimeError('Local colony placement is not instantiated')
            assignments.append({'colony': colony['id'], 'host': local['host_id'], 'verified_instance_roots': len(actual)})
    evidence = {'state': 'PLACEMENT_VERIFIED', 'observed_capacity': local, 'observed_peers': observations, 'assignments': assignments,
                'selection_measure': 'Observed runnable load per available CPU, among actual source-compatible hosts',
                'cross_host_execution_observed': transport is not None}
    atomic_write(context.root / 'placement.json', canonical_bytes(evidence))
    return evidence
