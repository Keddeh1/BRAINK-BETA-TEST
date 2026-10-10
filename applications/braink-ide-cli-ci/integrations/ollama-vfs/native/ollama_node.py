"""Ollama execution attached to the owner's VFS; no replacement identity algebra."""
import json
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from uuid import uuid4
from braink_node.owner_vfs.store import VFSStore
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.canonical import canonical_bytes


def retain(root, path, document, actor):
    store = VFSStore(root)
    old = store.resolve_path(path)
    record, receipt = store.write(ArtifactWrite(path, canonical_bytes(document), actor,
        predecessor=old.digest if old else None, media_type='application/json'))
    if store.read_content(record.digest) != canonical_bytes(document):
        raise RuntimeError('VFS readback differs')
    return {'digest': record.digest, 'observer': store.verify(record.digest)}


def attach(root, actor, endpoint, parent_volume, model_volume):
    parsed = urlsplit(endpoint)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Runtime endpoint requires an HTTP transport')
    document = {'actor': actor, 'provider': 'ollama', 'endpoint': endpoint.rstrip('/'),
        'parent_volume': parent_volume, 'model_volume': model_volume,
        'mount_kind': 'REFERENCE', 'runtime_observation': 'NOT_OBSERVED'}
    return retain(root, '/actor/binding.json', document, actor)


def binding(root):
    store = VFSStore(root)
    record = store.resolve_path('/actor/binding.json')
    if record is None:
        raise ValueError('Placed actor binding absent')
    return json.loads(store.read_content(record.digest))


def execute(root, operation, payload=None, timeout=300):
    actor = binding(root)
    if operation not in ('inventory', 'chat'):
        raise ValueError('Unknown Ollama operation')
    invocation = '/executions/' + uuid4().hex
    document = {'actor': actor['actor'], 'operation': operation, 'payload': payload}
    request_receipt = retain(root, invocation + '/request.json', document, actor['actor'])
    request = Request(actor['endpoint'] + ('/api/tags' if operation == 'inventory' else '/api/chat'),
        data=None if operation == 'inventory' else canonical_bytes({**payload, 'stream': False}),
        headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        if operation == 'inventory' and not isinstance(result.get('models'), list):
            raise ValueError('Invalid Ollama inventory')
        if operation == 'chat' and (result.get('done') is not True or not isinstance(result.get('message', {}).get('content'), str)):
            raise ValueError('Inference completion not established')
    except Exception as error:
        state = 'UNREACHABLE_OR_INVALID' if operation == 'inventory' else 'OUTCOME_UNKNOWN'
        receipt = retain(root, invocation + '/result.json', {'state': state,
            'error_type': type(error).__name__, 'request_digest': request_receipt['digest']}, actor['actor'])
        return {'state': state, 'receipt': receipt, 'actor': actor['actor']}
    receipt = retain(root, invocation + '/result.json', {'state': 'RETURNED',
        'result': result, 'request_digest': request_receipt['digest']}, actor['actor'])
    return {'state': 'RETURNED', 'result': result, 'receipt': receipt, 'actor': actor['actor']}
