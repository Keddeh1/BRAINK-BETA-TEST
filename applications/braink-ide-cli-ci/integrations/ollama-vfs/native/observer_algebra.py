"""Owner-supplied observer algebra; exact rational coordinates preserve identity and frame."""
from fractions import Fraction
import argparse
import fcntl
import json
from pathlib import Path
from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.store import VFSStore
from ollama_node import retain


def number(value):
    if type(value) not in (int, str):
        raise TypeError('Exact coordinate requires an integer or rational string')
    return Fraction(value)


def frame(origin, orientation, anchor):
    if type(orientation) is not int or orientation not in (-1, 1):
        raise ValueError('Orientation must be -1 or +1')
    if not isinstance(anchor, str) or not anchor:
        raise ValueError('Explicit origin anchor required')
    return {'anchor': anchor, 'o': str(number(origin)), 'epsilon': orientation}


def observe(identity, observer, position, time):
    if not isinstance(identity, str) or not identity or time is None:
        raise ValueError('Identity and temporal context must be retained')
    observer = frame(observer['o'], observer['epsilon'], observer['anchor'])
    q = observer['epsilon'] * (number(position) - number(observer['o']))
    return {'I': identity, 'O': observer, 'q': str(q), 't': time}


def validate(state):
    if not isinstance(state, dict) or not isinstance(state.get('I'), str) or not state['I'] or state.get('t') is None:
        raise ValueError('Observation requires I, O, q and t')
    observer = frame(state['O']['o'], state['O']['epsilon'], state['O']['anchor'])
    number(state['q'])
    canonical_bytes(state)
    return observer


def operate(left, right, operation, result_identity, time):
    observer = validate(left)
    if validate(right) != observer:
        raise ValueError('Different observer frames require an explicit transformation')
    if not isinstance(result_identity, str) or not result_identity or time is None:
        raise ValueError('Explicit result identity and temporal context required')
    u, v = number(left['q']), number(right['q'])
    o, epsilon = number(observer['o']), observer['epsilon']
    if operation == 'coordinate_add': q = u + v
    elif operation == 'transported_add': q = u + v + epsilon * o
    elif operation == 'transported_multiply': q = epsilon*u*v + o*(u+v) + epsilon*(o*o-o)
    else: raise ValueError('Explicit supported operation required')
    return {'I': result_identity, 'O': observer, 'q': str(q), 't': time,
            'operation': operation, 'operands': [left, right]}


def reverse_orientation(state):
    observer = validate(state)
    return {**state, 'O': {**observer, 'epsilon': -observer['epsilon']}, 'q': str(-number(state['q']))}


def evaluate(root, actor, request, request_id):
    if not isinstance(request_id, str) or not request_id or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in request_id):
        raise ValueError('Explicit request identity must be a path segment')
    root = Path(root)
    if not (root / 'vfs.sqlite3').is_file():
        raise FileNotFoundError('Use an existing instance VFS')
    locks = root / 'observer-locks'
    locks.mkdir(exist_ok=True)
    with (locks / request_id).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        path = '/observer/operations/' + request_id + '.json'
        store = VFSStore(root)
        old = store.resolve_path(path)
        if old:
            document = json.loads(store.read_content(old.digest))
            if canonical_bytes(document['request']) != canonical_bytes(request):
                raise ValueError('Request identity has different observer input')
            return {'result': document['result'], 'receipt': store.verify(old.digest), 'replayed': True}
        result = operate(request['left'], request['right'], request['operation'], request['result_identity'], request['time'])
        receipt = retain(root, path, {'request': request, 'result': result}, actor)
        return {'result': result, 'receipt': receipt, 'replayed': False}


def publish(root, actor, request, request_id, config, recipient):
    """Apply the complete observer tuple to real native mesh delivery and custody."""
    from colony_lifecycle import services
    _, mesh = services(config)
    subscription = mesh.request('/subscription', {'instance': actor})
    result = evaluate(root, actor, request, request_id)
    anchor = {'type': 'RELATIONAL_ANCHOR', 'source': actor,
              'definition': subscription['definition_id'], 'relation': 'observer-state-operation',
              'uncertainty': [], 'contradiction': [], 'next_route': recipient,
              'observer_state': result['result']}
    exchanged = mesh.request('/exchange', {'sender': actor, 'recipient': recipient, 'row': anchor,
                                          'message_id': 'observer:' + actor + ':' + request_id})
    inbox = mesh.request('/inbox', {'instance': recipient, 'after': exchanged['sequence'] - 1})
    delivered = next((row for row in inbox if row['digest'] == exchanged['digest']), None)
    if delivered is None or delivered['document']['row']['observer_state'] != result['result']:
        raise ValueError('Observer tuple mesh readback differs')
    receipt = retain(root, '/observer/publications/' + request_id + '.json',
                     {'recipient': recipient, 'exchange': exchanged, 'observer_state': result['result']}, actor)
    return {'observer_state': result['result'], 'inbox_readback_verified': True, 'receipt': receipt}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--actor', required=True)
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--request-id', required=True)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--recipient')
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    if bool(args.config) != bool(args.recipient): parser.error('--config and --recipient must be supplied together')
    result = publish(args.root, args.actor, request, args.request_id, args.config, args.recipient) if args.recipient else evaluate(args.root, args.actor, request, args.request_id)
    print(json.dumps(result))


if __name__ == '__main__': main()
