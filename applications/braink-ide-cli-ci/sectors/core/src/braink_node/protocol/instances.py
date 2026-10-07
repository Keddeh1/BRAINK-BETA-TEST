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

        if state['state'] == 'READBACK':
            vfs.read_content(state['steps']['INSTANTIATE_VFS']['digest'])
            if not vfs.verify_receipt_chain()['verified']:
                raise RuntimeError('Instance VFS receipt chain differs')
            prefix = state['steps']['SUBSCRIBE_VFS']['prefix']
            self.hub.subscribe(instance, prefix)
            observed = self.mesh.request('/subscription', {'instance': instance})
            if observed['definition_sha256'] != definition['definition_sha256']:
                raise RuntimeError('Resumed IL-LLM subscription differs')
            published = state['steps']['READBACK']['actor']
            artifact_digest = published.get('artifact', published).get('digest', published.get('artifact_digest'))
            self.hub.readback(artifact_digest, prefix + '/ceremony.json')
            return state
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

    def invoke(self, instance, bindings, args=(), kwargs=None, context=None):
        """Execute a real callable and retain invocation evidence in its instance VFS."""
        from uuid import uuid4
        directory = self.root / instance
        state = json.loads((directory / 'ceremony.json').read_text())
        module_id = state['definition_id']
        definition = bindings.catalogue['modules'][module_id]
        if definition['definition_sha256'] != state['definition_sha256']:
            raise ValueError('Invocation definition differs from instantiated source')
        vfs = VFSStore(directory / 'vfs')
        invocation = '/invocations/' + uuid4().hex
        request = {'instance': instance, 'module': module_id, 'args': list(args), 'kwargs': kwargs or {}, 'context': context}
        try:
            request_bytes = canonical_bytes(request)
        except (TypeError, ValueError):
            request_bytes = canonical_bytes({'instance': instance, 'module': module_id, 'context': context,
                'argument_capture': 'LIVE_CONTEXT', 'argument_types': [type(value).__module__ + '.' + type(value).__qualname__ for value in args],
                'keyword_types': {key: type(value).__module__ + '.' + type(value).__qualname__ for key, value in (kwargs or {}).items()}})
        record, actor = vfs.write(ArtifactWrite(invocation + '/request.json', request_bytes, instance, media_type='application/json'))
        vfs.verify(record.digest)
        try:
            result = bindings.invoke(module_id, args, kwargs, context)
        except Exception as error:
            failure = {'state': 'RAISED', 'type': type(error).__name__, 'message': str(error), 'request_digest': record.digest}
            failed, _ = vfs.write(ArtifactWrite(invocation + '/result.json', canonical_bytes(failure), instance, media_type='application/json'))
            vfs.verify(failed.digest)
            raise
        try:
            payload = canonical_bytes({'state': 'RETURNED', 'value': result, 'request_digest': record.digest})
        except (TypeError, ValueError):
            # Preserve the live return value; do not fabricate serialization of an opaque object.
            payload = canonical_bytes({'state': 'RETURNED', 'value_type': type(result).__module__ + '.' + type(result).__qualname__,
                                       'value_capture': 'LIVE_CONTEXT', 'request_digest': record.digest})
        returned, _ = vfs.write(ArtifactWrite(invocation + '/result.json', payload, instance, media_type='application/json'))
        vfs.verify(returned.digest)
        return result

    def deploy(self, catalogue, sectors=('core', 'cli', 'ide', 'ci')):
        with (self.root / 'deployment.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            return self._deploy(catalogue, sectors)

    def _deploy(self, catalogue, sectors=('core', 'cli', 'ide', 'ci')):
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
        prior_path = self.root / 'deployment.json'
        prior = json.loads(prior_path.read_text()) if prior_path.exists() else {'instances': [], 'sectors': [], 'sector_catalogue_sha256': {}}
        updated_colonies = {'colony://braink-development/' + sector for sector in sectors}
        retained = [row for row in prior['instances'] if row['occurrence'][0] not in updated_colonies]
        manifest = {'schema': 'braink.colony-deployment.v1', 'catalogue_sha256': catalogue['definition_sha256'],
                    'sectors': sorted(set(sectors) | set(prior['sectors'])),
                    'sector_catalogue_sha256': {**prior.get('sector_catalogue_sha256', {}), **{sector: catalogue['definition_sha256'] for sector in sectors}},
                    'instances': retained + [{'instance': row['instance'], 'definition_id': row['definition_id'],
                                                         'state': row['state'], 'occurrence': row['occurrence']} for row in instances]}
        atomic_write(self.root / 'deployment.json', canonical_bytes(manifest))
        return manifest
