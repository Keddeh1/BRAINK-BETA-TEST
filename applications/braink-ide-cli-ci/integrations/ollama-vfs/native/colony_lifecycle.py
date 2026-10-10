"""Lifecycle services around the working VFS. KEX remains the owner's state seed."""
import argparse
import fcntl
import json
from pathlib import Path
from braink_node.canonical import canonical_bytes
from braink_node.owner_vfs.store import VFSStore
from braink_node.protocol.catalogue import digest
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.transport import HubSubscription, JSONTransport
from braink_node.storage import atomic_write
from ollama_node import retain


def services(config):
    config = json.loads(Path(config).read_text())
    hub = HubSubscription(JSONTransport(config['vfs_url'], Path(config['vfs_token_file']).read_text().strip()))
    mesh = JSONTransport(config['mesh_url'], Path(config['mesh_token_file']).read_text().strip())
    return hub, mesh


def definitions(deployment):
    catalogue = deployment['catalogue']
    result = dict(catalogue['modules'])
    for kind in ('families', 'variants', 'colonies'):
        result.update({row['id']: row for row in catalogue[kind]})
    return result


def inspect_instances(root, deployment):
    root = Path(root).resolve()
    indexed = definitions(deployment)
    rows = []
    for row in deployment['instances']:
        definition = indexed[row['definition_id']]
        expected = 'braink-' + digest({'definition': definition['definition_sha256'], 'occurrence': row['occurrence']})
        if row['instance'] != expected or row['definition_sha256'] != definition['definition_sha256']:
            raise ValueError('Instance identity or definition differs')
        backing = root / 'instances' / expected / 'vfs'
        if not (backing / 'vfs.sqlite3').is_file():
            raise FileNotFoundError('Native VFS backing absent: ' + expected)
        store = VFSStore(backing)
        retained = store.resolve_path('/definition.json')
        if retained is None or store.read_content(retained.digest) != canonical_bytes(definition):
            raise ValueError('Retained definition differs: ' + expected)
        if not store.verify_receipt_chain()['verified']:
            raise ValueError('Receipt chain differs: ' + expected)
        rows.append({'instance': expected, 'definition_id': definition['id'], 'vfs_root': str(backing),
                     'definition_digest': retained.digest, 'receipt_chain_verified': True})
    if len({row['instance'] for row in rows}) != len(rows):
        raise ValueError('Duplicate instance in deployment')
    return rows


def checkpoint(root):
    root = Path(root).resolve()
    with (root / 'lifecycle.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        deployment = json.loads((root / 'deployment.json').read_text())
        observed = inspect_instances(root, deployment)
        colony = next(row for row in deployment['instances'] if row['definition_id'].startswith('colony://'))
        path = '/lifecycle/generations/' + digest(deployment) + '.json'
        receipt = retain(root / 'instances' / colony['instance'] / 'vfs', path,
                         {'deployment': deployment, 'observed': observed}, colony['instance'])
        pointer = {'schema': 'braink.colony-recovery.v1', 'colony_instance': colony['instance'],
                   'snapshot_digest': receipt['digest'], 'snapshot_path': path}
        atomic_write(root / 'lifecycle-recovery.json', canonical_bytes(pointer))
        return {'state': 'CHECKPOINT_READBACK', 'instances': len(observed), 'pointer': pointer}


def recovery_snapshot(root):
    root = Path(root).resolve()
    pointer = json.loads((root / 'lifecycle-recovery.json').read_text())
    instance = pointer['colony_instance']
    if len(instance) != 71 or not instance.startswith('braink-') or any(c not in '0123456789abcdef' for c in instance[7:]):
        raise ValueError('Invalid recovery instance')
    backing = root / 'instances' / instance / 'vfs'
    if not (backing / 'vfs.sqlite3').is_file():
        raise FileNotFoundError('Recovery VFS backing absent')
    store = VFSStore(backing)
    if not store.verify_receipt_chain()['verified']:
        raise ValueError('Recovery receipt chain differs')
    snapshot = json.loads(store.read_content(pointer['snapshot_digest']))
    inspect_instances(root, snapshot['deployment'])
    return snapshot


def rehydrate(root, config):
    root = Path(root).resolve()
    with (root / 'lifecycle.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        snapshot = recovery_snapshot(root)
        deployment = snapshot['deployment']
        if (root / 'deployment.json').exists() and json.loads((root / 'deployment.json').read_text()) != deployment:
            raise ValueError('Current generation differs; checkpoint it before recovery')
        indexed = definitions(deployment)
        hub, mesh = services(config)
        manager = InstanceManager(root / 'instances', hub, mesh)
        resumed = []
        for row in deployment['instances']:
            state_path = root / 'instances' / row['instance'] / 'ceremony.json'
            if state_path.exists() and json.loads(state_path.read_text()) != row:
                raise ValueError('Ceremony differs from retained generation')
            # Restore a missing projection from its existing custodied snapshot, never new backing.
            if not state_path.exists():
                atomic_write(state_path, canonical_bytes(row))
            resumed.append(manager.instantiate(indexed[row['definition_id']], row['occurrence']))
        atomic_write(root / 'deployment.json', canonical_bytes(deployment))
        colony = next(row for row in resumed if row['definition_id'].startswith('colony://'))
        evidence = {'state': 'REHYDRATED_READBACK', 'instances': len(resumed),
                    'all_ceremonies_readback': all(row['state'] == 'READBACK' for row in resumed),
                    'backing_recreated': False, 'scope': 'Existing VFS backing and live hub/mesh subscriptions'}
        retain(root / 'instances' / colony['instance'] / 'vfs', '/lifecycle/latest-rehydration.json', evidence, colony['instance'])
        return evidence


def connect(root, config, sender, recipient, relation, message_id):
    root = Path(root).resolve()
    deployment = json.loads((root / 'deployment.json').read_text())
    valid = {row['instance'] for row in inspect_instances(root, deployment)}
    if sender not in valid or recipient not in valid:
        raise ValueError('Connection endpoints must be actual colony instances')
    if not isinstance(relation, str) or not relation or not isinstance(message_id, str) or not message_id:
        raise ValueError('Explicit relation and message identity required')
    _, mesh = services(config)
    sender_definition = next(row['definition_id'] for row in deployment['instances'] if row['instance'] == sender)
    anchor = {'type': 'RELATIONAL_ANCHOR', 'source': sender, 'definition': sender_definition, 'relation': relation,
              'next_route': recipient, 'uncertainty': [], 'contradiction': []}
    exchanged = mesh.request('/exchange', {'sender': sender, 'recipient': recipient, 'row': anchor, 'message_id': message_id})
    inbox = mesh.request('/inbox', {'instance': recipient, 'after': exchanged['sequence'] - 1})
    if not any(row['digest'] == exchanged['digest'] for row in inbox):
        raise ValueError('Connection inbox readback differs')
    return retain(root / 'instances' / sender / 'vfs', '/lifecycle/connections/' + digest(message_id) + '.json',
                  {'sender': sender, 'recipient': recipient, 'relation': relation, 'exchange': exchanged,
                   'inbox_readback_verified': True}, sender)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--config', type=Path)
    parser.add_argument('operation', choices=['checkpoint', 'rehydrate', 'status', 'connect'])
    parser.add_argument('--sender')
    parser.add_argument('--recipient')
    parser.add_argument('--relation')
    parser.add_argument('--message-id')
    args = parser.parse_args()
    if args.operation == 'checkpoint': result = checkpoint(args.root)
    elif args.operation == 'status': result = inspect_instances(args.root, json.loads((args.root / 'deployment.json').read_text()))
    elif args.operation == 'rehydrate':
        if args.config is None: parser.error('rehydrate requires --config')
        result = rehydrate(args.root, args.config)
    else:
        if not all((args.config, args.sender, args.recipient, args.relation, args.message_id)):
            parser.error('connect requires --config, --sender, --recipient, --relation and --message-id')
        result = connect(args.root, args.config, args.sender, args.recipient, args.relation, args.message_id)
    print(json.dumps(result))


if __name__ == '__main__': main()
