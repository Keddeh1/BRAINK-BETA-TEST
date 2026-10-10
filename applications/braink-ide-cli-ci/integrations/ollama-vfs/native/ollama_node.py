"""Ollama execution attached to the owner's VFS; no replacement identity algebra."""
import json
import fcntl
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from uuid import uuid4
from braink_node.owner_vfs.store import VFSStore
from braink_node.owner_vfs.model import ArtifactWrite
from braink_node.canonical import canonical_bytes


def retain(root, path, document, actor):
    store = VFSStore(root)
    old = store.resolve_path(path)
    if old and store.read_content(old.digest) == canonical_bytes(document):
        return {'digest': old.digest, 'observer': store.verify(old.digest)}
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


def mount_model_volume(root, child_root, volume, actor):
    """Reference a real child VFS definition; payload bytes remain in the child store."""
    child = VFSStore(child_root)
    definition = child.resolve_path('/definition.json')
    if definition is None:
        raise ValueError('Child VFS definition absent')
    child.read_content(definition.digest)
    if not child.verify_receipt_chain()['verified']:
        raise RuntimeError('Child VFS receipt chain differs')
    return retain(root, '/volumes/models.json', {'volume': volume,
        'child_root': str(Path(child_root).resolve()), 'definition_digest': definition.digest,
        'mount_kind': 'REFERENCE'}, actor)


def resolve_model_volume(root):
    parent = VFSStore(root)
    reference = parent.resolve_path('/volumes/models.json')
    if reference is None:
        raise ValueError('Model volume reference absent')
    document = json.loads(parent.read_content(reference.digest))
    child = VFSStore(document['child_root'])
    child.read_content(document['definition_digest'])
    return document


def execute(root, operation, payload=None, timeout=300, request_id=None):
    actor = binding(root)
    routes = {'inventory': '/api/tags', 'chat': '/api/chat', 'show': '/api/show', 'pull': '/api/pull'}
    if operation not in routes:
        raise ValueError('Unknown Ollama operation')
    if operation != 'inventory' and not isinstance(payload, dict):
        raise ValueError('Operation payload must be an object')
    identity = request_id or uuid4().hex
    if not identity or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in identity):
        raise ValueError('Request identity must be a path segment')
    lock_dir = Path(root) / 'execution-locks'
    lock_dir.mkdir(exist_ok=True)
    with (lock_dir / identity).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return dispatch(root, actor, operation, payload, timeout, identity, routes[operation])


def dispatch(root, actor, operation, payload, timeout, identity, route):
    store = VFSStore(root)
    invocation = '/executions/' + identity
    document = {'actor': actor['actor'], 'operation': operation, 'payload': payload}
    old = store.resolve_path(invocation + '/request.json')
    if old:
        if store.read_content(old.digest) != canonical_bytes(document):
            raise ValueError('Existing execution identity has different input')
        result_record = store.resolve_path(invocation + '/result.json')
        if result_record:
            result = json.loads(store.read_content(result_record.digest))
            return {**result, 'receipt': {'digest': result_record.digest,
                'observer': store.verify(result_record.digest)}, 'actor': actor['actor'], 'replayed': True}
        # A persisted dispatch may have executed before the process stopped. Do not execute twice.
        return {'state': 'OUTCOME_UNKNOWN', 'actor': actor['actor'], 'request_digest': old.digest, 'replayed': True}
    request_receipt = retain(root, invocation + '/request.json', document, actor['actor'])
    request = Request(actor['endpoint'] + route,
        data=None if operation == 'inventory' else canonical_bytes({**payload, 'stream': False}),
        headers={'Content-Type': 'application/json'})
    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.load(response)
        if result.get('error'):
            raise ValueError('Ollama returned a provider error')
        if operation == 'inventory' and not isinstance(result.get('models'), list):
            raise ValueError('Invalid Ollama inventory')
        if operation == 'chat' and (result.get('done') is not True or not isinstance(result.get('message', {}).get('content'), str)):
            raise ValueError('Inference completion not established')
        if operation == 'pull' and result.get('status') != 'success':
            raise ValueError('Model pull completion not established')
    except HTTPError as error:
        observation = {'state': 'PROVIDER_HTTP_ERROR', 'http_status': error.code}
    except Exception as error:
        observation = {'state': 'UNREACHABLE_OR_INVALID' if operation in ('inventory','show') else 'OUTCOME_UNKNOWN',
            'error_type': type(error).__name__}
    else:
        observation = {'state': 'RETURNED', 'result': result}
    observation['request_digest'] = request_receipt['digest']
    receipt = retain(root, invocation + '/result.json', observation, actor['actor'])
    return {**observation, 'receipt': receipt, 'actor': actor['actor']}
