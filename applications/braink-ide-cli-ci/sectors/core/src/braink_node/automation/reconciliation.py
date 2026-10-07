from pathlib import Path
import json
from braink_node.owner_vfs.store import VFSStore
from braink_node.protocol.catalogue import digest


def expected_instances(catalogue):
    definitions = dict(catalogue['modules'])
    for kind in ('families', 'variants', 'colonies'):
        definitions.update({row['id']: row for row in catalogue[kind]})
    result = {}
    for colony in catalogue['colonies']:
        occurrences = [(colony['id'], [colony['id']])]
        for variant_id in colony['variants']:
            variant = definitions[variant_id]
            occurrences.append((variant_id, [colony['id'], variant_id]))
            for family_id in variant['families']:
                family = definitions[family_id]
                occurrences.append((family_id, [colony['id'], variant_id, family_id]))
                occurrences.extend((module, [colony['id'], variant_id, family_id, module]) for module in family['modules'])
        for definition_id, occurrence in occurrences:
            definition = definitions[definition_id]
            instance = 'braink-' + digest({'definition': definition['definition_sha256'], 'occurrence': occurrence})
            result[instance] = {'instance': instance, 'definition_id': definition_id, 'definition_sha256': definition['definition_sha256'], 'occurrence': occurrence}
    return result


def run(context):
    expected = expected_instances(context.catalogue())
    deployed = {row['instance']: row for row in context.deployment()['instances']}
    findings, checked = [], 0
    for instance, row in deployed.items():
        directory = context.state / 'instances' / instance
        try:
            state = json.loads((directory / 'ceremony.json').read_text())
            store = VFSStore(directory / 'vfs')
            if state['state'] != 'READBACK':
                findings.append({'instance': instance, 'kind': 'CEREMONY_INTERRUPTED', 'state': state['state']})
            if not store.verify_receipt_chain()['verified']:
                findings.append({'instance': instance, 'kind': 'RECEIPT_CONTRADICTION'})
            definition = json.loads(store.read_content(state['steps']['INSTANTIATE_VFS']['digest']))
            if definition['definition_sha256'] != state['definition_sha256']:
                findings.append({'instance': instance, 'kind': 'DEFINITION_CONTRADICTION'})
            checked += 1
        except Exception as error:
            findings.append({'instance': instance, 'kind': 'INSTANCE_READ_ERROR', 'exception': type(error).__name__, 'reason': str(error)})
    for instance in expected.keys() - deployed.keys():
        findings.append({'instance': instance, 'kind': 'REVISION_NOT_DEPLOYED', **expected[instance]})
    return {'state': 'ALIGNED' if not findings else 'DISCREPANCIES', 'checked': checked, 'expected': len(expected),
            'catalogue_sha256': context.catalogue()['definition_sha256'], 'findings': findings,
            'retained_prior_revisions': sorted(deployed.keys() - expected.keys())}
