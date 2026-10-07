import base64
import hashlib
import json
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.owner_vfs.store import VFSStore


def run(context):
    verified, mirrored, errors = 0, 0, []
    pages = {}
    for row in context.deployment()['instances']:
        instance = row['instance']
        try:
            state = json.loads((context.state / 'instances' / instance / 'ceremony.json').read_text())
            prefix = state['steps']['SUBSCRIBE_VFS']['prefix']
            subscription = context.hub.subscribe(instance, prefix)
            if subscription['prefix'] != prefix:
                raise RuntimeError('Subscription prefix differs')
            cursor = subscription['cursor']
            store = VFSStore(context.state / 'instances' / instance / 'vfs')
            while True:
                if cursor not in pages:
                    pages[cursor] = context.hub_transport.request('/events?after=' + str(cursor) + '&limit=1000')
                events = pages[cursor]
                for event in events.get('events', []):
                    if event.get('path', '').startswith(prefix + '/') and event.get('artifact_digest'):
                        artifact = context.hub_transport.request('/artifacts/' + event['artifact_digest'])
                        content = base64.b64decode(artifact['content_b64'], validate=True)
                        if hashlib.sha256(content).hexdigest() != event['artifact_digest']:
                            raise RuntimeError('Subscription artifact differs')
                        path = '/subscription-mirror/' + event['artifact_digest']
                        if store.resolve_path(path) is None:
                            store.write(ArtifactWrite(path, content, instance))
                            mirrored += 1
                next_cursor = events.get('next_cursor', cursor)
                if next_cursor == cursor:
                    break
                cursor = next_cursor
            observed = context.hub_transport.request('/subscriptions', {'subscriber': instance, 'prefix': prefix, 'cursor': cursor})
            if observed['cursor'] != cursor:
                raise RuntimeError('Cursor readback differs')
            verified += 1
        except Exception as error:
            errors.append({'instance': instance, 'exception': type(error).__name__, 'reason': str(error)})
    return {'state': 'CONTINUOUS' if not errors else 'RETRY_REQUIRED', 'subscriptions_verified': verified, 'mirrored_artifacts': mirrored, 'errors': errors, 'verified_event_pages': len(pages), 'continuity_window': 'Each observed cursor is drained through the owner event feed until an empty verified page is read.'}
