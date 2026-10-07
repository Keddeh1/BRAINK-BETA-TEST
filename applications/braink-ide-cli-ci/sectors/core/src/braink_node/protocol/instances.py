"""Instances own distinct VFS stores and independently read back both subscriptions."""
import json
import fcntl
from pathlib import Path

from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore
from braink_node.protocol.catalogue import digest
from braink_node.storage import atomic_write


class InstanceManager:
    def __init__(self, root, hub, mesh):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.hub = hub
        self.mesh = mesh

    def instantiate(self, definition, occurrence):
        instance = 'braink-' + digest({'definition': definition['definition_sha256'], 'occurrence': occurrence})
        directory = self.root / instance
        directory.mkdir(exist_ok=True)
        with (directory / 'ceremony.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._instantiate(definition, occurrence)

    def _instantiate(self, definition, occurrence):
        identity = {'definition': definition['definition_sha256'], 'occurrence': occurrence}
        instance = 'braink-' + digest(identity)
        directory = self.root / instance
        directory.mkdir(exist_ok=True)
        state_path = directory / 'ceremony.json'
        state = json.loads(state_path.read_text()) if state_path.exists() else {
            'schema': 'braink.instance.v1', 'instance': instance, 'definition_id': definition['id'],
            'definition_sha256': definition['definition_sha256'], 'occurrence': occurrence, 'steps': {}, 'state': 'DECLARED'}
        vfs = VFSStore(directory / 'vfs')

        def checkpoint(stage, evidence):
            state['steps'][stage] = evidence
            state['state'] = stage
            atomic_write(state_path, canonical_bytes(state))

        if 'INSTANTIATE_VFS' not in state['steps']:
            record, actor = vfs.write(ArtifactWrite('/definition.json', canonical_bytes(definition), instance, media_type='application/json'))
            checkpoint('INSTANTIATE_VFS', {'root': str(directory / 'vfs'), 'digest': record.digest,
                                           'actor': actor.as_dict(), 'observer': vfs.verify(record.digest)})
        else:
            vfs.read_content(state['steps']['INSTANTIATE_VFS']['digest'])
        prefix = '/applications/braink-development/instances/' + instance
        checkpoint('SUBSCRIBE_VFS', self.hub.subscribe(instance, prefix))
        request = {'instance': instance, 'definition_id': definition['id'], 'definition_sha256': definition['definition_sha256'],
                   'vfs_prefix': prefix, 'relations': definition.get('modules', definition.get('families', definition.get('variants', [])))}
        self.mesh.request('/subscribe', request)
        subscription = self.mesh.request('/subscription', {'instance': instance})
        if subscription['definition_sha256'] != definition['definition_sha256'] or subscription['instance'] != instance:
            raise RuntimeError('IL-LLM subscription readback differs')
        checkpoint('SUBSCRIBE_IL_LLM_NETWORK_MESH', subscription)
        evidence = self.hub.publish(instance, prefix + '/ceremony.json', state)
        if not vfs.verify_receipt_chain()['verified']:
            raise RuntimeError('Instance VFS receipt chain differs')
        checkpoint('READBACK', evidence)
        return state

    def deploy(self, catalogue, sectors=('core', 'cli', 'ide', 'ci')):
        definitions = {**catalogue['modules']}
        for kind in ('families', 'variants', 'colonies'):
            definitions.update({row['id']: row for row in catalogue[kind]})
        instances = []
        for colony in catalogue['colonies']:
            if colony['sector'] not in sectors:
                continue
            for variant_id in colony['variants']:
                variant = definitions[variant_id]
                for family_id in variant['families']:
                    family = definitions[family_id]
                    for module_id in family['modules']:
                        instances.append(self.instantiate(definitions[module_id], [colony['id'], variant_id, family_id, module_id]))
                    instances.append(self.instantiate(family, [colony['id'], variant_id, family_id]))
                instances.append(self.instantiate(variant, [colony['id'], variant_id]))
            instances.append(self.instantiate(colony, [colony['id']]))
        manifest = {'schema': 'braink.colony-deployment.v1', 'catalogue_sha256': catalogue['definition_sha256'],
                    'sectors': list(sectors), 'instances': [{'instance': row['instance'], 'definition_id': row['definition_id'],
                                                         'state': row['state'], 'occurrence': row['occurrence']} for row in instances]}
        atomic_write(self.root / 'deployment.json', canonical_bytes(manifest))
        return manifest
